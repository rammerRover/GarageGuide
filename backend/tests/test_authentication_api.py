from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import psycopg
import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app import authentication, database, security, session_queries, user_queries
from app.config import AuthConfigurationError, AuthSettings, get_auth_settings
from app.routes.auth import AuthenticationRoute
from app.schemas import RegistrationResponse
from app.session_queries import create_session as real_create_session
from app.user_queries import verify_user_credentials as real_verify_credentials
from authentication_support import AUTH_HEADERS, CSRF_CASES, AuthenticationInput, csrf_headers


pytestmark = pytest.mark.usefixtures("forbid_database")
NOW = datetime(2026, 11, 6, tzinfo=timezone.utc)


@pytest.fixture
def account():
    return AuthenticationInput()


@pytest.fixture
def queries(monkeypatch):
    user = RegistrationResponse(id=7, email="user@example.com", created_at=NOW)
    actor = session_queries.AuthenticatedSession(user, 11, NOW + timedelta(minutes=30))
    issued = session_queries.IssuedSession(actor, security.generate_session_token())

    def issue(settings, *, user, presented_token=None, prepare_response=None):
        prepare_response(issued)
        return issued

    mocks = {
        "verify": Mock(return_value=user), "issue": Mock(side_effect=issue),
        "extend": Mock(return_value=actor), "revoke": Mock(),
        "register": Mock(return_value=(user.id, user.email, user.created_at)),
    }
    for owner, name, key in (
        (user_queries, "verify_user_credentials", "verify"),
        (user_queries, "create_user", "register"),
        (session_queries, "create_session", "issue"),
        (session_queries, "validate_and_extend_session", "extend"),
        (session_queries, "revoke_session", "revoke"),
    ):
        monkeypatch.setattr(owner, name, mocks[key])
    return mocks


def test_login_success_returns_public_only_and_session_cookie(client, account, queries, caplog):
    response = account.login(client)
    assert response.status_code == 200
    assert account.result(response) == {
        "user": {"id": 7, "email": "user@example.com", "created_at": "2026-11-06T00:00:00Z"},
        "expires_at": "2026-11-06T00:30:00Z",
    }
    account.token(response)
    cookie = response.headers["set-cookie"].lower()
    flags_correct = (
        "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie
        and all(flag not in cookie for flag in ("domain=", "max-age=", "expires=", "secure"))
    )
    assert flags_correct
    account.assert_safe(response, caplog)


@pytest.mark.parametrize("known", [False, True], ids=["unknown-account", "wrong-password"])
def test_generic_credentials_failure_does_not_disturb_existing_cookie(
    client, account, queries, caplog, monkeypatch, known
):
    old = security.generate_session_token()
    account.install_cookie(client, old)
    monkeypatch.setattr(user_queries, "verify_user_credentials", real_verify_credentials)
    connection = Mock()
    connection.execute.return_value.fetchone.return_value = (
        (7, "user@example.com", NOW, "synthetic-encoded-hash") if known else None
    )

    @contextmanager
    def connect(settings, *, read_only):
        assert read_only
        yield connection

    monkeypatch.setattr(database, "connect_database", connect)
    verify = Mock(return_value=False)
    monkeypatch.setattr(security._PASSWORD_HASH, "verify", verify)
    response = account.login(client)
    assert response.status_code == 401
    assert account.result(response) == {"detail": "Invalid email or password."}
    assert verify.call_count == 1 and queries["issue"].call_count == 0
    unchanged = client.cookies.get("garageguide_session") == old.get_secret_value()
    assert unchanged and "set-cookie" not in response.headers
    account.assert_safe(response, caplog)


@pytest.mark.parametrize("changes", [
    {"email": "invalid"}, {"password": chr(0x61) * 14}, {"password": chr(0x61) * 129},
    {"password": {"private": chr(0x61) * 15}}, {"password": chr(0xD800) * 15},
    {"user_id": 99}, {"password_confirmation": chr(0x61) * 15},
])
def test_login_validation_is_sanitized_before_lookup(client, account, queries, caplog, changes):
    response = account.login(client, changes=changes)
    assert response.status_code == 422
    details = account.result(response)["detail"]
    safe = all(set(entry) == {"loc", "msg", "type"} for entry in details)
    assert safe
    assert queries["verify"].call_count == queries["issue"].call_count == 0
    account.assert_safe(response, caplog)


def test_malformed_login_json_is_sanitized(client, account, queries, caplog):
    response = account.login(client, malformed=True)
    assert response.status_code == 422
    account.assert_safe(response, caplog)
    queries["verify"].assert_not_called()


@pytest.mark.parametrize("path", ["register", "login", "logout"])
@pytest.mark.parametrize("case", CSRF_CASES)
def test_every_csrf_denial_precedes_body_parsing_and_business_operations(
    client, account, queries, caplog, path, case
):
    response = account.send(
        client, "POST", "/api/auth/" + path, content="{malformed-private-body",
        headers=csrf_headers(case),
    )
    assert response.status_code == 403
    assert account.result(response) == {"detail": "Request not allowed."}
    assert "set-cookie" not in response.headers
    assert all(query.call_count == 0 for query in queries.values())
    account.assert_safe(response, caplog)


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://127.0.0.1:4173"])
def test_registration_remains_usable_with_required_headers(client, account, queries, caplog, origin):
    from registration_support import RegistrationInput

    response = RegistrationInput().send(client)
    assert response.status_code == 201
    response = account.login(client, headers={**AUTH_HEADERS, "Origin": origin,
                                             "Content-Type": "application/json; charset=utf-8"})
    assert response.status_code == 200
    account.assert_safe(response, caplog)


@pytest.mark.parametrize("source", ["verify", "issue", "extend", "revoke"])
@pytest.mark.parametrize("error_type", [psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled])
def test_availability_failures_are_503_without_cookie_changes(
    client, account, queries, caplog, source, error_type
):
    old = security.generate_session_token()
    account.install_cookie(client, old)
    queries[source].side_effect = account.failure(error_type)
    if source in ("verify", "issue"):
        response = account.login(client)
    else:
        response = account.send(client, "GET" if source == "extend" else "POST",
                                "/api/auth/session" if source == "extend" else "/api/auth/logout", content="{}")
    assert response.status_code == 503
    assert account.result(response) == {"detail": "Authentication unavailable. Please try again."}
    unchanged = client.cookies.get("garageguide_session") == old.get_secret_value()
    assert unchanged and "set-cookie" not in response.headers
    account.assert_safe(response, caplog)


@pytest.mark.parametrize("source", ["verify", "issue", "extend", "revoke"])
def test_unexpected_failures_are_generic_and_never_escape(client, account, queries, caplog, source):
    account.install_cookie(client, security.generate_session_token())
    queries[source].side_effect = account.failure()
    if source in ("verify", "issue"):
        response = account.login(client)
    else:
        response = account.send(client, "GET" if source == "extend" else "POST",
                                "/api/auth/session" if source == "extend" else "/api/auth/logout", content="{}")
    assert response.status_code == 500
    assert account.result(response) == {"detail": "Internal server error"}
    assert "set-cookie" not in response.headers
    account.assert_safe(response, caplog)


@pytest.mark.parametrize("commit_fails", [False, True])
def test_cookie_is_delivered_only_after_session_commit(client, account, queries, monkeypatch, caplog, commit_fails):
    events = []
    connection = Mock()
    connection.execute.side_effect = [
        Mock(fetchone=lambda: (NOW,)), Mock(), Mock(fetchone=lambda: (11, NOW + timedelta(minutes=30))),
    ]

    @contextmanager
    def connect(settings, *, read_only):
        assert not read_only
        events.append("open")
        try:
            yield connection
            events.append("commit")
            if commit_fails:
                raise account.failure(psycopg.OperationalError)
        except BaseException:
            events.append("rollback")
            raise
        finally:
            events.append("close")

    original_cookie = authentication.set_session_cookie

    def prepare_cookie(*args):
        events.append("cookie-prepared")
        original_cookie(*args)

    monkeypatch.setattr(database, "connect_database", connect)
    monkeypatch.setattr(session_queries, "create_session", real_create_session)
    monkeypatch.setattr(authentication, "set_session_cookie", prepare_cookie)
    response = account.login(client)
    assert response.status_code == (503 if commit_fails else 200)
    assert events == (["open", "cookie-prepared", "commit", "rollback", "close"]
                      if commit_fails else ["open", "cookie-prepared", "commit", "close"])
    assert ("set-cookie" in response.headers) == (not commit_fails)
    account.assert_safe(response, caplog)


def test_session_uses_cookie_and_reusable_dependency_without_mutation_headers(client, account, queries, caplog):
    token = security.generate_session_token()
    account.install_cookie(client, token)
    response = account.send(client, "GET", "/api/auth/session?user_id=999")
    assert response.status_code == 200
    assert account.result(response)["user"]["id"] == 7
    supplied_token = queries["extend"].call_args.args[1] == token
    assert supplied_token
    protected = APIRouter(route_class=AuthenticationRoute)

    @protected.get("/api/test-private")
    def private(actor=Depends(authentication.require_authenticated_session)):
        return {"id": actor.user.id}

    client.app.include_router(protected)
    future = account.send(client, "GET", "/api/test-private?user_id=999")
    assert future.status_code == 200 and account.result(future) == {"id": 7}
    account.assert_safe(response, caplog)
    account.assert_safe(future, caplog)


@pytest.mark.parametrize("state", ["missing", "malformed", "unknown", "expired", "revoked"])
def test_session_rejections_share_401_and_clear_cookie(client, account, queries, monkeypatch, caplog, state):
    if state != "missing":
        account.install_cookie(client, SecretStr("malformed-cookie") if state == "malformed"
                               else security.generate_session_token())
    if state in ("missing", "malformed"):
        monkeypatch.setattr(session_queries, "validate_and_extend_session", real_validate)
        no_hash = Mock(side_effect=AssertionError("Malformed cookie reached hashing"))
        monkeypatch.setattr(security, "hash_session_token", no_hash)
    else:
        queries["extend"].side_effect = session_queries.InvalidSessionError()
    response = account.send(client, "GET", "/api/auth/session")
    assert response.status_code == 401
    assert account.result(response) == {"detail": "Not authenticated."}
    deletion = "max-age=0" in response.headers.get("set-cookie", "").lower()
    assert deletion and not client.cookies.get("garageguide_session")
    account.assert_safe(response, caplog)


real_validate = session_queries.validate_and_extend_session


@pytest.mark.parametrize("state", ["missing", "malformed", "valid"])
def test_logout_is_empty_204_and_clears_only_current_cookie(client, account, queries, caplog, state):
    if state != "missing":
        account.install_cookie(client, SecretStr("malformed-cookie") if state == "malformed"
                               else security.generate_session_token())
    for _ in range(2):
        response = account.send(client, "POST", "/api/auth/logout", content="{}")
        assert response.status_code == 204 and response.content == b""
        deletion = "max-age=0" in response.headers.get("set-cookie", "").lower()
        assert deletion and not client.cookies.get("garageguide_session")
        account.assert_safe(response, caplog)


@pytest.mark.parametrize("endpoint", ["register", "login", "session", "logout"])
def test_bad_auth_configuration_fails_closed_without_affecting_health(client, account, queries, caplog, endpoint):
    def invalid():
        raise AuthConfigurationError()

    client.app.dependency_overrides[get_auth_settings] = invalid
    response = account.send(client, "GET" if endpoint == "session" else "POST",
                            "/api/auth/" + endpoint, content="{}")
    assert response.status_code == 503 and "set-cookie" not in response.headers
    assert all(query.call_count == 0 for query in queries.values())
    account.assert_safe(response, caplog)
    assert client.get("/api/health").status_code == 200


def test_production_cookie_is_secure_and_deleted_with_matching_scope(client, account, queries, caplog):
    client.app.dependency_overrides[get_auth_settings] = lambda: AuthSettings(
        "production", True, "https://garage.example", "https://garage.example"
    )
    with TestClient(client.app, base_url="https://garage.example") as secure_client:
        headers = {**AUTH_HEADERS, "Origin": "https://garage.example"}
        issued = account.login(secure_client, headers=headers)
        assert issued.status_code == 200
        account.token(issued)
        cookie = issued.headers.get("set-cookie", "").lower()
        flags_correct = "secure" in cookie and "domain=" not in cookie
        assert flags_correct
        removed = account.send(secure_client, "POST", "/api/auth/logout", content="{}", headers=headers)
        deletion = removed.headers.get("set-cookie", "").lower()
        flags_correct = "secure" in deletion and "max-age=0" in deletion and "domain=" not in deletion
        assert removed.status_code == 204 and flags_correct
        account.assert_safe(issued, caplog)
        account.assert_safe(removed, caplog)


@pytest.mark.parametrize("path,status", [("/api/auth/login", 405), ("/api/auth/unknown", 404)])
def test_auth_routing_errors_also_prevent_caching(client, path, status):
    response = client.get(path)
    assert response.status_code == status
    assert response.headers.get("cache-control") == "no-store"
