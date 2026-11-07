from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from time import monotonic

import pytest
from pydantic import SecretStr

from app import database, security, session_queries, user_queries
from app.schemas import LoginRequest, RegistrationResponse


pytestmark = pytest.mark.integration


@pytest.fixture
def accounts(native_database):
    secret = SecretStr(chr(0xE9) * 15)
    encoded = security.validate_and_hash_credentials(secret, secret)
    result = []
    for _ in range(2):
        email = native_database.reserve_email()
        row = user_queries.create_user(native_database.settings, email=email, password_hash=encoded)
        user = RegistrationResponse(id=row[0], email=row[1], created_at=row[2])
        native_database.track_user(user.id, user.email)
        result.append(user)
    return result


def issue(native, user, previous=None):
    result = session_queries.create_session(native.settings, user=user, presented_token=previous)
    native.track_session(result.session.session_id, user.id)
    return result


def session_row(native, session_id):
    with native.connect(native.settings, read_only=True) as connection:
        return connection.execute(
            "SELECT id, user_id, token_hash, created_at, expires_at, revoked_at "
            "FROM public.user_sessions WHERE id = %s", (session_id,),
        ).fetchone()


def test_real_credentials_return_only_public_identity(native_database, accounts):
    request = LoginRequest(
        email=" \t" + accounts[0].email.upper() + "\n",
        password=SecretStr((chr(0x65) + chr(0x301)) * 15),
    )
    user = user_queries.verify_user_credentials(native_database.settings, request)
    assert user == accounts[0]
    assert set(user.model_dump()) == {"id", "email", "created_at"}
    wrong = LoginRequest(email=accounts[0].email, password=SecretStr(chr(0x61) * 15))
    assert user_queries.verify_user_credentials(native_database.settings, wrong) is None
    unknown = LoginRequest(email=native_database.reserve_email(), password=request.password)
    assert user_queries.verify_user_credentials(native_database.settings, unknown) is None


def test_committed_session_uses_database_time_and_only_token_hash(native_database, accounts):
    issued = issue(native_database, accounts[0])
    row = session_row(native_database, issued.session.session_id)
    assert row[1] == accounts[0].id
    hashed_only = (
        row[2] == security.hash_session_token(issued.token)
        and row[2] != issued.token.get_secret_value()
        and len(row[2]) == 64 and row[2] == row[2].lower()
    )
    assert hashed_only
    assert row[3].tzinfo is not None and row[4] - row[3] == timedelta(minutes=30)
    assert row[5] is None


def test_replacement_cleans_only_invalid_owned_sessions_and_preserves_other_devices(native_database, accounts):
    first, second = accounts
    old, other = issue(native_database, first), issue(native_database, first)
    other_user, other_invalid = issue(native_database, second), issue(native_database, second)
    expired, revoked = issue(native_database, first), issue(native_database, first)
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "UPDATE public.user_sessions SET created_at = clock_timestamp() - INTERVAL '1 hour', "
            "expires_at = clock_timestamp() - INTERVAL '1 minute' WHERE id = %s AND user_id = %s",
            (expired.session.session_id, first.id),
        )
        connection.execute(
            "UPDATE public.user_sessions SET revoked_at = clock_timestamp() "
            "WHERE id = ANY(%s) AND user_id = ANY(%s)",
            ([revoked.session.session_id, other_invalid.session.session_id], [first.id, second.id]),
        )
    replacement = issue(native_database, first, old.token)
    assert session_row(native_database, old.session.session_id) is None
    assert session_row(native_database, expired.session.session_id) is None
    assert session_row(native_database, revoked.session.session_id) is None
    assert session_row(native_database, other.session.session_id)[5] is None
    assert session_row(native_database, other_user.session.session_id)[5] is None
    assert session_row(native_database, other_invalid.session.session_id)[5] is not None
    assert replacement.token != old.token


def test_switching_accounts_revokes_only_presented_browser(native_database, accounts):
    old, independent = issue(native_database, accounts[0]), issue(native_database, accounts[0])
    second_device = issue(native_database, accounts[1])
    replacement = issue(native_database, accounts[1], old.token)
    assert session_row(native_database, old.session.session_id)[5] is not None
    assert session_row(native_database, independent.session.session_id)[5] is None
    assert session_row(native_database, second_device.session.session_id)[5] is None
    actor = session_queries.validate_and_extend_session(native_database.settings, replacement.token)
    assert actor.user.id == accounts[1].id


def test_unknown_cookie_does_not_revoke_existing_sessions(native_database, accounts):
    existing = issue(native_database, accounts[0])
    issue(native_database, accounts[0], security.generate_session_token())
    assert session_row(native_database, existing.session.session_id)[5] is None


def test_failed_response_preparation_rolls_back_replacement_cleanup_and_insert(native_database, accounts):
    old, invalid = issue(native_database, accounts[0]), issue(native_database, accounts[0])
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "UPDATE public.user_sessions SET revoked_at = clock_timestamp() WHERE id = %s AND user_id = %s",
            (invalid.session.session_id, accounts[0].id),
        )

    def fail_before_commit(result):
        raise RuntimeError("Synthetic pre-commit preparation failure")

    with pytest.raises(RuntimeError, match="pre-commit"):
        session_queries.create_session(
            native_database.settings, user=accounts[0], presented_token=old.token,
            prepare_response=fail_before_commit,
        )
    assert session_row(native_database, old.session.session_id)[5] is None
    assert session_row(native_database, invalid.session.session_id)[5] is not None
    with native_database.connect(native_database.settings, read_only=True) as connection:
        count = connection.execute(
            "SELECT count(*) FROM public.user_sessions WHERE user_id = %s", (accounts[0].id,),
        ).fetchone()[0]
    assert count == 2


@pytest.mark.parametrize("boundary", [
    "idle-before", "idle-equal", "idle-after", "absolute-before", "absolute-equal",
    "absolute-after", "revoked",
])
def test_strict_expiry_boundaries_and_absolute_extension_cap(native_database, accounts, monkeypatch, boundary):
    issued = issue(native_database, accounts[0])
    with native_database.connect(native_database.settings) as connection:
        now = connection.execute("SELECT clock_timestamp()").fetchone()[0]
        offset = {"before": 1, "equal": 0, "after": -1}.get(boundary.split("-")[-1], 1)
        if boundary.startswith("absolute"):
            created = now - timedelta(hours=8) + timedelta(seconds=offset)
            expires = now + timedelta(minutes=10)
        else:
            created = now - timedelta(hours=1)
            expires = now + timedelta(seconds=offset)
        connection.execute(
            "UPDATE public.user_sessions SET created_at = %s, expires_at = %s, revoked_at = %s "
            "WHERE id = %s AND user_id = %s",
            (created, expires, now if boundary == "revoked" else None,
             issued.session.session_id, accounts[0].id),
        )
    # Freeze a PostgreSQL-generated instant to prove equality without timing races.
    monkeypatch.setattr(session_queries, "_database_time", lambda connection: now)
    valid = boundary.endswith("before")
    if valid:
        actor = session_queries.validate_and_extend_session(native_database.settings, issued.token)
        assert actor.expires_at == min(now + timedelta(minutes=30), created + timedelta(hours=8))
    else:
        with pytest.raises(session_queries.InvalidSessionError):
            session_queries.validate_and_extend_session(native_database.settings, issued.token)
    stored = session_row(native_database, issued.session.session_id)
    assert stored[3] == created
    assert stored[4] == (actor.expires_at if valid else expires)
    assert (stored[5] is not None) == (boundary == "revoked")


def test_real_activity_extends_and_commits_before_return(native_database, accounts):
    issued = issue(native_database, accounts[0])
    actor = session_queries.validate_and_extend_session(native_database.settings, issued.token)
    row = session_row(native_database, actor.session_id)
    assert actor.user == accounts[0]
    assert actor.expires_at == row[4] and row[4] >= issued.session.expires_at
    assert row[4] <= row[3] + timedelta(hours=8)


def test_logout_revokes_current_only_and_is_idempotent(native_database, accounts):
    current, other = issue(native_database, accounts[0]), issue(native_database, accounts[0])
    session_queries.revoke_session(native_database.settings, current.token)
    revoked_at = session_row(native_database, current.session.session_id)[5]
    assert revoked_at is not None
    session_queries.revoke_session(native_database.settings, current.token)
    session_queries.revoke_session(native_database.settings, None)
    session_queries.revoke_session(native_database.settings, security.generate_session_token())
    assert session_row(native_database, current.session.session_id)[5] == revoked_at
    assert session_row(native_database, other.session.session_id)[5] is None
    with pytest.raises(session_queries.InvalidSessionError):
        session_queries.validate_and_extend_session(native_database.settings, current.token)


@pytest.mark.parametrize("change", ["revoked", "expired"])
def test_waiting_extension_cannot_revive_session(native_database, accounts, monkeypatch, change):
    issued = issue(native_database, accounts[0])
    opened = Event()
    worker_pid = []

    def worker_connect(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        worker_pid.append(connection.info.backend_pid)
        opened.set()
        return connection

    def extend():
        try:
            session_queries.validate_and_extend_session(native_database.settings, issued.token)
            return "incorrectly-authenticated"
        except session_queries.InvalidSessionError:
            return "rejected"
        except Exception:
            return "unexpected-failure-redacted"

    monkeypatch.setattr(database, "connect_database", worker_connect)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with native_database.connect(native_database.settings) as locker:
            locker.execute(
                "SELECT id FROM public.user_sessions WHERE id = %s AND user_id = %s FOR UPDATE",
                (issued.session.session_id, accounts[0].id),
            )
            future = pool.submit(extend)
            assert opened.wait(timeout=2)
            deadline = monotonic() + 1.5
            blocked = False
            while monotonic() < deadline:
                blocked = locker.execute(
                    "SELECT %s = ANY(pg_blocking_pids(%s))",
                    (locker.info.backend_pid, worker_pid[0]),
                ).fetchone()[0]
                if blocked:
                    break
                Event().wait(0.01)
            assert blocked, "PostgreSQL did not confirm the expected row-lock wait"
            if change == "revoked":
                locker.execute(
                    "UPDATE public.user_sessions SET revoked_at = clock_timestamp() "
                    "WHERE id = %s AND user_id = %s",
                    (issued.session.session_id, accounts[0].id),
                )
            else:
                # Set expiry after the worker's transaction/locking statement began.
                locker.execute(
                    "UPDATE public.user_sessions SET expires_at = clock_timestamp() "
                    "WHERE id = %s AND user_id = %s",
                    (issued.session.session_id, accounts[0].id),
                )
        assert future.result(timeout=5) == "rejected"
    row = session_row(native_database, issued.session.session_id)
    assert (row[5] is not None) == (change == "revoked")
    with pytest.raises(session_queries.InvalidSessionError):
        session_queries.validate_and_extend_session(native_database.settings, issued.token)


def test_exact_cleanup_recovers_committed_session_after_lost_response(native_database, accounts):
    with pytest.raises(RuntimeError, match="lost response"):
        session_queries.create_session(native_database.settings, user=accounts[0])
        raise RuntimeError("Synthetic lost response before fixture tracking")
    native_database.cleanup()
    assert native_database.cleanup_verified
    assert native_database.cleanup_counts == (2, 1)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        assert connection.execute(
            "SELECT count(*) FROM public.user_sessions WHERE user_id = ANY(%s)",
            ([user.id for user in accounts],),
        ).fetchone() == (0,)
