from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import Mock

import psycopg
import pytest
from fastapi.exceptions import RequestValidationError

from app import database, security, user_queries
from app.config import get_settings
from registration_support import RegistrationInput


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture
def account():
    return RegistrationInput()


@pytest.fixture
def query(monkeypatch):
    create = Mock(return_value=(7, "user@example.com", datetime(2026, 11, 4, tzinfo=timezone.utc)))
    monkeypatch.setattr(user_queries, "create_user", create)
    return create


def test_success_uses_existing_normalization_and_hashing(client, account, query, caplog):
    response = account.send(client)
    assert response.status_code == 201
    public_result = account.result(response) == {
        "id": 7, "email": "user@example.com", "created_at": "2026-11-04T00:00:00Z"
    }
    assert public_result
    used_normalized_email = query.call_count == 1 and query.call_args.kwargs["email"] == "user@example.com"
    assert used_normalized_email
    hash_verified = account.verifies_hash(query.call_args.kwargs["password_hash"])
    assert hash_verified
    no_session = "set-cookie" not in response.headers and not response.cookies
    assert no_session
    account.assert_redacted(response, caplog)


@pytest.mark.parametrize(
    "case",
    ["missing-email", "missing-password", "missing-password_confirmation",
     "empty-password", "empty-password_confirmation", "invalid-email",
     "password-object", "confirmation-list", "short", "long", "mismatch",
     "invalid-unicode", "body-list", "malformed-json", "invalid-utf8"],
)
def test_validation_errors_are_safe_and_never_query(client, account, query, caplog, case):
    response = account.send(client, case)
    assert response.status_code == 422
    details = account.result(response).get("detail")
    has_safe_details = isinstance(details, list) and bool(details) and all(
        set(error) == {"loc", "msg", "type"} and
        error["loc"] in (["body"], ["body", "email"], ["body", "password"], ["body", "password_confirmation"])
        for error in details
    )
    assert has_safe_details
    did_not_query = query.call_count == 0
    assert did_not_query
    if case == "mismatch":
        targets_confirmation = details[0]["loc"] == ["body", "password_confirmation"]
        assert targets_confirmation
    account.assert_redacted(response, caplog)


@pytest.mark.parametrize("source", ["query", "hashing", "dependency", "response"])
def test_unexpected_errors_never_escape_or_log_private_data(
    client, account, query, caplog, monkeypatch, source
):
    failure = account.failure()
    if source == "query":
        query.side_effect = failure
    elif source == "hashing":
        def broken_hash(*args):
            raise failure
        monkeypatch.setattr(security, "validate_and_hash_credentials", broken_hash)
    elif source == "dependency":
        def broken_settings():
            raise failure
        client.app.dependency_overrides[get_settings] = broken_settings
    else:
        query.return_value = (account.hash_marker, "user@example.com", None)
    response = account.send(client)
    assert response.status_code == 500
    generic = account.result(response) == {"detail": "Internal server error"}
    assert generic
    account.assert_redacted(response, caplog)


@pytest.mark.parametrize(
    "error_type",
    [psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled],
    ids=["connection", "connection-interface", "statement-timeout"],
)
def test_database_availability_errors_are_generic_503(
    client, account, query, caplog, error_type
):
    query.side_effect = account.failure(error_type)
    response = account.send(client)
    assert response.status_code == 503
    generic = account.result(response) == {
        "detail": "Registration unavailable. Please try again."
    }
    assert generic
    account.assert_redacted(response, caplog)


def test_normal_duplicate_is_approved_409(client, account, query, caplog):
    query.side_effect = user_queries.DuplicateEmailError()
    response = account.send(client)
    assert response.status_code == 409
    approved = account.result(response) == {
        "detail": "An account with this email already exists."
    }
    assert approved
    account.assert_redacted(response, caplog)


@pytest.mark.parametrize("constraint", ["users_email_key", "another_constraint"])
def test_unique_constraint_response_follows_rollback_and_close(
    client, account, caplog, monkeypatch, constraint
):
    events = []
    connection = Mock()
    failure = account.failure(
        psycopg.errors.UniqueViolation,
        info={psycopg.pq.DiagnosticField.CONSTRAINT_NAME: constraint.encode()},
    )
    connection.execute.side_effect = [Mock(fetchone=lambda: None), failure]

    @contextmanager
    def connect(settings, *, read_only):
        try:
            yield connection
            events.append("commit")
        except BaseException:
            events.append("rollback")
            raise
        finally:
            events.append("close")

    monkeypatch.setattr(database, "connect_database", connect)
    response = account.send(client)
    assert response.status_code == (409 if constraint == "users_email_key" else 500)
    assert events == ["rollback", "close"]
    account.assert_redacted(response, caplog)


@pytest.mark.parametrize("commit_fails", [False, True], ids=["committed", "commit-failed"])
def test_201_requires_commit_and_connection_close(client, account, caplog, monkeypatch, commit_fails):
    events = []
    connection = Mock()
    connection.execute.side_effect = [
        Mock(fetchone=lambda: None),
        Mock(fetchone=lambda: (7, "user@example.com", datetime(2026, 11, 4, tzinfo=timezone.utc))),
    ]

    @contextmanager
    def connect(settings, *, read_only):
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

    monkeypatch.setattr(database, "connect_database", connect)
    response = account.send(client)
    assert response.status_code == (503 if commit_fails else 201)
    assert events == (["commit", "rollback", "close"] if commit_fails else ["commit", "close"])
    account.assert_redacted(response, caplog)


@pytest.mark.parametrize("unhashable_metadata", [False, True])
def test_unknown_validation_metadata_is_never_reflected(client, account, query, caplog, unhashable_metadata):
    field = [account.driver_marker] if unhashable_metadata else account.driver_marker
    error_type = [account.hash_marker] if unhashable_metadata else account.hash_marker
    query.side_effect = RequestValidationError([{
        "loc": ("body", field), "type": error_type,
        "msg": account.driver_marker, "input": account.driver_marker,
        "ctx": {"private": account.hash_marker},
    }])
    response = account.send(client)
    assert response.status_code == 422
    safe_fallback = account.result(response) == {
        "detail": [{"loc": ["body"], "msg": "Enter a valid value.", "type": "value_error"}]
    }
    assert safe_fallback
    account.assert_redacted(response, caplog)


def test_unapproved_credential_message_is_not_reflected(client, account, query, caplog, monkeypatch):
    def invalid_credentials(*args):
        raise security.CredentialValidationError("password", account.driver_marker)

    monkeypatch.setattr(security, "validate_and_hash_credentials", invalid_credentials)
    response = account.send(client)
    assert response.status_code == 422
    safe_fallback = account.result(response) == {
        "detail": [{"loc": ["body", "password"], "msg": "Enter valid credentials.", "type": "value_error"}]
    }
    assert safe_fallback
    account.assert_redacted(response, caplog)
