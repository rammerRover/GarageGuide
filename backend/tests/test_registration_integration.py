from datetime import datetime

import psycopg
import pytest

from app import database, user_queries
from registration_support import RegistrationInput


pytestmark = pytest.mark.integration


@pytest.fixture
def account(native_database):
    email = native_database.reserve_email()
    return RegistrationInput(" \t" + email.upper() + "\n")


def test_api_success_is_committed_public_and_session_free(client, account, native_database, caplog):
    response = account.send(client)
    assert response.status_code == 201
    public = account.result(response)
    expected_keys = set(public) == {"id", "email", "created_at"}
    assert expected_keys
    with database.connect_database(native_database.settings, read_only=True) as connection:
        stored = connection.execute(
            "SELECT id, email, password_hash, created_at FROM public.users WHERE id = %s",
            (public["id"],),
        ).fetchone()
        session_count = connection.execute(
            "SELECT count(*) FROM public.user_sessions WHERE user_id = %s", (public["id"],)
        ).fetchone()
    matches_database = stored is not None and stored[0] == public["id"] and stored[1] == public["email"]
    assert matches_database
    timestamp_matches = datetime.fromisoformat(public["created_at"].replace("Z", "+00:00")) == stored[3]
    assert timestamp_matches
    hash_verified = account.verifies_hash(stored[2])
    assert hash_verified
    no_session = session_count == (0,) and "set-cookie" not in response.headers and not response.cookies
    assert no_session
    account.assert_redacted(response, caplog)


def test_normal_and_forced_unique_duplicates_return_409(client, account, native_database, caplog, monkeypatch):
    first = account.send(client)
    assert first.status_code == 201
    for force_database_constraint in (False, True):
        with monkeypatch.context() as patch:
            if force_database_constraint:
                patch.setattr(user_queries, "find_user_id", lambda connection, email: None)
            duplicate = account.send(client)
        assert duplicate.status_code == 409
        approved = account.result(duplicate) == {
            "detail": "An account with this email already exists."
        }
        assert approved
        account.assert_redacted(duplicate, caplog)
    email = account.result(first)["email"]
    with database.connect_database(native_database.settings, read_only=True) as connection:
        assert connection.execute(
            "SELECT count(*) FROM public.users WHERE email = %s", (email,)
        ).fetchone() == (1,)


@pytest.mark.parametrize("case", ["short", "mismatch", "invalid-unicode", "malformed-json"])
def test_invalid_api_request_creates_no_account(client, account, native_database, caplog, case):
    response = account.send(client, case)
    assert response.status_code == 422
    with database.connect_database(native_database.settings, read_only=True) as connection:
        assert connection.execute(
            "SELECT id FROM public.users WHERE email = %s", (account.email.strip().lower(),)
        ).fetchone() is None
    account.assert_redacted(response, caplog)


def test_database_failure_rolls_back_before_503_and_retry_succeeds(
    client, account, native_database, caplog, monkeypatch
):
    original = user_queries.insert_user

    def insert_then_fail(connection, email, password_hash):
        original(connection, email, password_hash)
        raise account.failure(psycopg.OperationalError)

    with monkeypatch.context() as patch:
        patch.setattr(user_queries, "insert_user", insert_then_fail)
        failure = account.send(client)
    assert failure.status_code == 503
    account.assert_redacted(failure, caplog)
    with database.connect_database(native_database.settings, read_only=True) as connection:
        assert connection.execute(
            "SELECT id FROM public.users WHERE email = %s", (account.email.strip().lower(),)
        ).fetchone() is None
    retry = account.send(client)
    assert retry.status_code == 201
    account.assert_redacted(retry, caplog)
