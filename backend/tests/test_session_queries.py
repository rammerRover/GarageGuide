from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import psycopg
import pytest
from pydantic import SecretStr

from app import database, security, session_queries, user_queries
from app.config import Settings, TEST_DATABASE
from app.schemas import LoginRequest, RegistrationResponse


pytestmark = pytest.mark.usefixtures("forbid_database")
NOW = datetime(2026, 11, 6, tzinfo=timezone.utc)


@pytest.fixture
def settings():
    return Settings("unused", 5432, TEST_DATABASE, "synthetic", "")


@pytest.fixture
def user():
    return RegistrationResponse(id=7, email="user@example.com", created_at=NOW)


@pytest.fixture
def transaction(monkeypatch):
    connection = Mock()
    events, fail_commit = [], []

    @contextmanager
    def connect(settings, *, read_only):
        events.append("read" if read_only else "write")
        try:
            yield connection
            events.append("commit")
            if fail_commit:
                raise psycopg.OperationalError("Synthetic commit failure")
        except BaseException:
            events.append("rollback")
            raise
        finally:
            events.append("close")

    monkeypatch.setattr(database, "connect_database", connect)
    return connection, events, fail_commit


def rows(connection, *values):
    connection.execute.side_effect = [Mock(fetchone=Mock(return_value=value)) for value in values]


@pytest.mark.parametrize("known", [False, True])
@pytest.mark.parametrize("matches", [False, True])
def test_credentials_lookup_closes_read_transaction_before_verification(
    settings, user, transaction, monkeypatch, known, matches
):
    connection, events, _ = transaction
    credentials = LoginRequest(email=" \tUser@EXAMPLE.COM\n", password=SecretStr(chr(0x61) * 15))
    stored = "synthetic-encoded-hash"
    rows(connection, (user.id, user.email, user.created_at, stored) if known else None)
    calls = []

    def verify(password, encoded):
        calls.append((password, encoded))
        assert events == ["read", "commit", "close"]
        return known and matches

    monkeypatch.setattr(security, "verify_credentials", verify)
    result = user_queries.verify_user_credentials(settings, credentials)
    assert result == (user if known and matches else None)
    correct_call = len(calls) == 1 and calls[0][1] == (stored if known else None)
    assert correct_call
    assert connection.execute.call_args.args == (
        "SELECT id, email, created_at, password_hash FROM public.users WHERE email = %s",
        ("user@example.com",),
    )
    safe_result = stored not in repr(result)
    assert safe_result


def test_credential_lookup_failure_closes_before_propagating(settings, transaction, monkeypatch):
    connection, events, _ = transaction
    connection.execute.side_effect = psycopg.OperationalError("Synthetic unavailable")
    verify = Mock()
    monkeypatch.setattr(security, "verify_credentials", verify)
    request = LoginRequest(email="user@example.com", password=SecretStr(chr(0x61) * 15))
    with pytest.raises(psycopg.OperationalError):
        user_queries.verify_user_credentials(settings, request)
    assert events == ["read", "rollback", "close"]
    verify.assert_not_called()


def test_new_session_binds_only_hash_and_prepares_before_commit(settings, user, transaction):
    connection, events, _ = transaction
    rows(connection, (NOW,), None, (11, NOW + timedelta(minutes=30)))
    prepared = []

    def prepare(result):
        assert events == ["write"]
        prepared.append(result.session.public_response().model_dump_json())

    issued = session_queries.create_session(settings, user=user, prepare_response=prepare)
    assert events == ["write", "commit", "close"]
    assert len(prepared) == 1
    calls = connection.execute.call_args_list
    assert calls[0].args == ("SELECT clock_timestamp()",)
    assert calls[1].args[1] == (user.id, NOW, NOW)
    insert_sql, insert_parameters = calls[2].args
    assert "clock_timestamp()" in insert_sql and "INTERVAL '30 minutes'" in insert_sql
    only_hash = insert_parameters == (user.id, security.hash_session_token(issued.token))
    raw_absent = all(issued.token.get_secret_value() not in repr(call.args) for call in calls)
    safe_repr = issued.token.get_secret_value() not in repr(issued)
    assert only_hash and raw_absent and safe_repr


def test_replacement_locks_before_sampling_time_and_revokes_only_valid_current(settings, user, transaction):
    connection, events, _ = transaction
    old = security.generate_session_token()
    rows(connection, (10,), (NOW,), None, (NOW,), None, (11, NOW + timedelta(minutes=30)))
    issued = session_queries.create_session(settings, user=user, presented_token=old)
    calls = connection.execute.call_args_list
    assert "FOR UPDATE" in calls[0].args[0]
    assert calls[1].args == ("SELECT clock_timestamp()",)
    revoke_sql, revoke_parameters = calls[2].args
    assert "revoked_at IS NULL" in revoke_sql
    assert "%s < expires_at" in revoke_sql and "%s < created_at + INTERVAL '8 hours'" in revoke_sql
    assert revoke_parameters == (NOW, 10, NOW, NOW)
    cleanup_sql, cleanup_parameters = calls[4].args
    assert "WHERE user_id = %s" in cleanup_sql and "revoked_at IS NOT NULL" in cleanup_sql
    assert "expires_at <= %s" in cleanup_sql and "INTERVAL '8 hours' <= %s" in cleanup_sql
    assert cleanup_parameters == (user.id, NOW, NOW)
    fresh = issued.token != old
    assert fresh
    assert events == ["write", "commit", "close"]


@pytest.mark.parametrize("failure", ["insert", "missing-row", "prepare", "commit"])
def test_creation_failures_rollback_and_close_without_returning_token(settings, user, transaction, failure):
    connection, events, fail_commit = transaction
    rows(connection, (NOW,), None, None if failure == "missing-row" else (11, NOW))
    if failure == "insert":
        connection.execute.side_effect = psycopg.OperationalError("Synthetic failure")
    if failure == "commit":
        fail_commit.append(True)

    def prepare(result):
        if failure == "prepare":
            raise RuntimeError("Synthetic response preparation failure")

    with pytest.raises((psycopg.OperationalError, RuntimeError)):
        session_queries.create_session(settings, user=user, prepare_response=prepare)
    assert events[-2:] == ["rollback", "close"]


def test_extension_locks_then_samples_time_rechecks_and_commits_identity(settings, user, transaction):
    connection, events, _ = transaction
    rows(connection, (11,), (NOW,), (user.id, NOW + timedelta(minutes=30)),
         (user.id, user.email, user.created_at))
    actor = session_queries.validate_and_extend_session(settings, security.generate_session_token())
    calls = connection.execute.call_args_list
    assert "FOR UPDATE" in calls[0].args[0]
    assert calls[1].args == ("SELECT clock_timestamp()",)
    sql, parameters = calls[2].args
    assert "LEAST(%s + INTERVAL '30 minutes', created_at + INTERVAL '8 hours')" in sql
    assert "revoked_at IS NULL AND %s < expires_at" in sql
    assert "%s < created_at + INTERVAL '8 hours'" in sql
    assert parameters == (NOW, 11, NOW, NOW)
    assert calls[3].args[1] == (user.id,)
    assert actor.user == user and actor.session_id == 11
    assert events == ["write", "commit", "close"]
    assert set(actor.public_response().model_dump()) == {"user", "expires_at"}


@pytest.mark.parametrize("failure", ["unknown", "invalid", "missing-user", "database", "commit"])
def test_extension_failure_never_returns_actor_and_closes(settings, user, transaction, failure):
    connection, events, fail_commit = transaction
    rows(connection, None if failure == "unknown" else (11,), (NOW,),
         None if failure == "invalid" else (user.id, NOW),
         None if failure == "missing-user" else (user.id, user.email, user.created_at))
    if failure == "database":
        connection.execute.side_effect = psycopg.OperationalError("Synthetic failure")
    if failure == "commit":
        fail_commit.append(True)
    with pytest.raises((session_queries.InvalidSessionError, psycopg.OperationalError)):
        session_queries.validate_and_extend_session(settings, security.generate_session_token())
    assert events[-2:] == ["rollback", "close"]


def test_missing_token_is_rejected_without_connecting(settings, transaction):
    _, events, _ = transaction
    with pytest.raises(session_queries.InvalidSessionError):
        session_queries.validate_and_extend_session(settings, None)
    session_queries.revoke_session(settings, None)
    assert events == []


@pytest.mark.parametrize("found", [False, True])
def test_revocation_is_current_session_only_and_idempotent(settings, transaction, found):
    connection, events, _ = transaction
    rows(connection, (11,) if found else None, (NOW,), None)
    session_queries.revoke_session(settings, security.generate_session_token())
    calls = connection.execute.call_args_list
    assert "FOR UPDATE" in calls[0].args[0]
    if found:
        assert calls[1].args == ("SELECT clock_timestamp()",)
        assert calls[2].args == (
            "UPDATE public.user_sessions SET revoked_at = %s WHERE id = %s AND revoked_at IS NULL",
            (NOW, 11),
        )
    else:
        assert len(calls) == 1
    assert events == ["write", "commit", "close"]
