import json

import psycopg
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app import security, session_queries
from authentication_support import AUTH_HEADERS, CSRF_CASES, AuthenticationInput, csrf_headers
from registration_support import RegistrationInput


pytestmark = pytest.mark.integration


@pytest.fixture
def accounts(client, native_database):
    result = []
    for _ in range(2):
        email = native_database.reserve_email()
        registration = RegistrationInput(" \t" + email.upper() + "\n")
        response = registration.send(client)
        assert response.status_code == 201
        user = registration.result(response)
        native_database.track_user(user["id"], email)
        result.append((AuthenticationInput(" \t" + email.upper() + "\n"), user))
    return result


def tracked_login(native, client, account, user):
    response = account.login(client)
    assert response.status_code == 200
    assert account.result(response)["user"] == user
    token = account.token(response)
    with native.connect(native.settings, read_only=True) as connection:
        row = connection.execute(
            "SELECT id FROM public.user_sessions WHERE user_id = %s AND token_hash = %s",
            (user["id"], security.hash_session_token(token)),
        ).fetchone()
    assert row is not None
    native.track_session(row[0], user["id"])
    return response, token, row[0]


def stored_session(native, session_id):
    with native.connect(native.settings, read_only=True) as connection:
        return connection.execute(
            "SELECT expires_at, revoked_at FROM public.user_sessions WHERE id = %s", (session_id,),
        ).fetchone()


def test_login_cookie_restores_committed_identity_and_extends_idle_deadline(
    client, accounts, native_database, caplog
):
    account, user = accounts[0]
    login, token, session_id = tracked_login(native_database, client, account, user)
    assert set(account.result(login)) == {"user", "expires_at"}
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "UPDATE public.user_sessions SET expires_at = clock_timestamp() + INTERVAL '1 minute' "
            "WHERE id = %s AND user_id = %s", (session_id, user["id"]),
        )
    before = stored_session(native_database, session_id)
    # A new client with only the browser cookie simulates restoration after refresh.
    with TestClient(client.app, base_url="http://127.0.0.1:8000") as restored:
        account.install_cookie(restored, token)
        response = account.send(restored, "GET", "/api/auth/session?user_id=999")
    assert response.status_code == 200
    public = account.result(response)
    assert public["user"] == user and set(public) == {"user", "expires_at"}
    after = stored_session(native_database, session_id)
    assert after[0] > before[0] and after[1] is None
    account.assert_safe(login, caplog)
    account.assert_safe(response, caplog)


def test_failed_credentials_preserve_existing_valid_session(client, accounts, native_database, caplog):
    account, user = accounts[0]
    _, old, session_id = tracked_login(native_database, client, account, user)
    unknown = native_database.reserve_email()
    for changes in ({"password": chr(0x61) * 15}, {"email": unknown}):
        response = account.login(client, changes=changes)
        assert response.status_code == 401
        assert account.result(response) == {"detail": "Invalid email or password."}
        unchanged = client.cookies.get("garageguide_session") == old.get_secret_value()
        assert unchanged and "set-cookie" not in response.headers
        assert stored_session(native_database, session_id)[1] is None
        account.assert_safe(response, caplog)
    restored = account.send(client, "GET", "/api/auth/session")
    assert restored.status_code == 200 and account.result(restored)["user"] == user


@pytest.mark.parametrize("state", ["missing", "malformed", "unknown", "expired", "revoked"])
def test_unusable_sessions_are_401_and_clear_cookie(client, accounts, native_database, caplog, state):
    account, user = accounts[0]
    if state in ("expired", "revoked"):
        _, token, session_id = tracked_login(native_database, client, account, user)
        if state == "expired":
            with native_database.connect(native_database.settings) as connection:
                connection.execute(
                    "UPDATE public.user_sessions SET created_at = clock_timestamp() - INTERVAL '1 hour', "
                    "expires_at = clock_timestamp() - INTERVAL '1 minute' WHERE id = %s AND user_id = %s",
                    (session_id, user["id"]),
                )
        else:
            session_queries.revoke_session(native_database.settings, token)
    elif state != "missing":
        account.install_cookie(client, SecretStr("malformed-cookie") if state == "malformed"
                               else security.generate_session_token())
    response = account.send(client, "GET", "/api/auth/session")
    assert response.status_code == 401
    assert account.result(response) == {"detail": "Not authenticated."}
    cleared = not client.cookies.get("garageguide_session") and "max-age=0" in response.headers["set-cookie"].lower()
    assert cleared
    account.assert_safe(response, caplog)


def test_account_switch_logout_and_two_browser_isolation(client, accounts, native_database, caplog):
    first, first_user = accounts[0]
    second, second_user = accounts[1]
    _, old, old_id = tracked_login(native_database, client, first, first_user)
    with TestClient(client.app, base_url="http://127.0.0.1:8000") as other_device, \
            TestClient(client.app, base_url="http://127.0.0.1:8000") as other_user:
        _, _, independent_id = tracked_login(native_database, other_device, first, first_user)
        tracked_login(native_database, other_user, second, second_user)
        switched, replacement, new_id = tracked_login(native_database, client, second, second_user)
        assert old != replacement and old_id != new_id
        assert stored_session(native_database, old_id)[1] is not None
        assert stored_session(native_database, independent_id)[1] is None
        current = second.send(client, "GET", "/api/auth/session?user_id=" + str(first_user["id"]))
        assert current.status_code == 200 and second.result(current)["user"] == second_user
        for _ in range(2):
            logout = second.send(client, "POST", "/api/auth/logout", content="{}")
            assert logout.status_code == 204 and logout.content == b""
            assert not client.cookies.get("garageguide_session")
            second.assert_safe(logout, caplog)
        assert stored_session(native_database, new_id)[1] is not None
        assert first.result(first.send(other_device, "GET", "/api/auth/session"))["user"] == first_user
        assert second.result(second.send(other_user, "GET", "/api/auth/session"))["user"] == second_user
        first.install_cookie(client, old)
        rejected = first.send(client, "GET", "/api/auth/session")
        assert rejected.status_code == 401
        first.assert_safe(rejected, caplog)
        second.assert_safe(switched, caplog)


@pytest.mark.parametrize("source", ["login", "session", "logout"])
def test_availability_failure_rolls_back_and_preserves_cookie_then_recovers(
    client, accounts, native_database, caplog, monkeypatch, source
):
    account, user = accounts[0]
    _, old, session_id = tracked_login(native_database, client, account, user)
    before = stored_session(native_database, session_id)
    with monkeypatch.context() as patch:
        if source == "login":
            original = session_queries._remove_invalid_sessions

            def cleanup_then_fail(*args):
                original(*args)
                raise account.failure(psycopg.OperationalError)

            patch.setattr(session_queries, "_remove_invalid_sessions", cleanup_then_fail)
            response = account.login(client)
        elif source == "session":
            def fail_serialization(*args):
                raise account.failure(psycopg.OperationalError)

            patch.setattr(session_queries.AuthenticatedSession, "public_response", fail_serialization)
            response = account.send(client, "GET", "/api/auth/session")
        else:
            original = session_queries._revoke_locked

            def revoke_then_fail(*args, **kwargs):
                original(*args, **kwargs)
                raise account.failure(psycopg.OperationalError)

            patch.setattr(session_queries, "_revoke_locked", revoke_then_fail)
            response = account.send(client, "POST", "/api/auth/logout", content="{}")
    assert response.status_code == 503
    assert account.result(response) == {"detail": "Authentication unavailable. Please try again."}
    unchanged = client.cookies.get("garageguide_session") == old.get_secret_value()
    assert unchanged and "set-cookie" not in response.headers
    assert stored_session(native_database, session_id) == before
    account.assert_safe(response, caplog)
    recovered = account.send(client, "GET", "/api/auth/session")
    assert recovered.status_code == 200 and account.result(recovered)["user"] == user


def test_unexpected_credential_failure_is_generic_and_preserves_session(client, accounts, native_database, caplog):
    account, user = accounts[0]
    _, old, _ = tracked_login(native_database, client, account, user)
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "UPDATE public.users SET password_hash = %s WHERE id = %s AND email = %s",
            ("synthetic private driver details", user["id"], user["email"]),
        )
    response = account.login(client)
    assert response.status_code == 500
    assert account.result(response) == {"detail": "Internal server error"}
    unchanged = client.cookies.get("garageguide_session") == old.get_secret_value()
    assert unchanged and "set-cookie" not in response.headers
    account.assert_safe(response, caplog)


@pytest.mark.parametrize("path", ["register", "login", "logout"])
@pytest.mark.parametrize("case", CSRF_CASES)
def test_native_csrf_denials_leave_no_synthetic_account_or_session(
    client, native_database, caplog, path, case
):
    email = native_database.reserve_email()
    account = AuthenticationInput(email)
    content = json.dumps({"email": email, "password": chr(0x61) * 15,
                          "password_confirmation": chr(0x61) * 15})
    response = account.send(client, "POST", "/api/auth/" + path, content=content, headers=csrf_headers(case))
    assert response.status_code == 403
    assert account.result(response) == {"detail": "Request not allowed."}
    with native_database.connect(native_database.settings, read_only=True) as connection:
        assert connection.execute(
            "SELECT id FROM public.users WHERE email = %s", (email,),
        ).fetchone() is None
        assert connection.execute(
            "SELECT s.id FROM public.user_sessions AS s JOIN public.users AS u ON u.id = s.user_id "
            "WHERE u.email = %s", (email,),
        ).fetchone() is None
    assert "set-cookie" not in response.headers
    account.assert_safe(response, caplog)


def test_rejected_logout_does_not_revoke_current_session(client, accounts, native_database, caplog):
    account, user = accounts[0]
    _, old, session_id = tracked_login(native_database, client, account, user)
    response = account.send(client, "POST", "/api/auth/logout", content="{}",
                            headers={**AUTH_HEADERS, "Origin": "null"})
    assert response.status_code == 403 and "set-cookie" not in response.headers
    assert stored_session(native_database, session_id)[1] is None
    unchanged = client.cookies.get("garageguide_session") == old.get_secret_value()
    assert unchanged
    account.assert_safe(response, caplog)


@pytest.mark.parametrize("state", ["missing", "malformed", "unknown", "expired", "revoked"])
def test_logout_unusable_sessions_remains_idempotent_204(client, accounts, native_database, caplog, state):
    account, user = accounts[0]
    if state in ("expired", "revoked"):
        _, token, session_id = tracked_login(native_database, client, account, user)
        with native_database.connect(native_database.settings) as connection:
            if state == "expired":
                connection.execute(
                    "UPDATE public.user_sessions SET created_at = clock_timestamp() - INTERVAL '1 hour', "
                    "expires_at = clock_timestamp() - INTERVAL '1 minute' WHERE id = %s AND user_id = %s",
                    (session_id, user["id"]),
                )
            else:
                session_queries.revoke_session(native_database.settings, token)
    elif state != "missing":
        account.install_cookie(client, SecretStr("malformed-cookie") if state == "malformed"
                               else security.generate_session_token())
    for _ in range(2):
        response = account.send(client, "POST", "/api/auth/logout", content="{}")
        assert response.status_code == 204 and response.content == b""
        assert not client.cookies.get("garageguide_session")
        account.assert_safe(response, caplog)
