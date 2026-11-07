from unittest.mock import MagicMock, Mock

import pytest

from app.config import Settings, TEST_DATABASE
from app.security import generate_session_token
from database_support import NativeTestDatabase, TestDatabaseSafetyError


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture
def settings():
    return Settings("unused", 5432, TEST_DATABASE, "synthetic", "")


def connection_with(*rows):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.execute.side_effect = [
        Mock(fetchone=Mock(return_value=row), fetchall=Mock(return_value=row)) for row in rows
    ]
    return connection


def test_cleanup_recovers_lost_session_and_deletes_exact_owned_records(settings):
    lookup = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [(8, "synthetic-hash")], None, None)
    reader = connection_with((TEST_DATABASE,), [], [])
    native = NativeTestDatabase(settings, Mock(side_effect=[lookup, writer, reader]))
    email = native.reserve_email()
    native.cleanup()
    safe_delete = writer.execute.call_args_list[-2].args == (
        "DELETE FROM public.user_sessions WHERE id = %s AND user_id = %s AND token_hash = %s",
        (8, 42, "synthetic-hash"),
    )
    assert safe_delete
    assert writer.execute.call_args_list[-1].args[1] == (42, email)
    assert reader.execute.call_args_list[-1].args[1] == ([8], [42])
    assert native.cleanup_verified and native.cleanup_counts == (1, 1)


@pytest.mark.parametrize("remaining", ["user", "session"])
def test_cleanup_never_claims_success_when_owned_records_remain(settings, remaining):
    lookup = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [], None)
    reader = connection_with((TEST_DATABASE,), [(42,)] if remaining == "user" else [],
                             [(8,)] if remaining == "session" else [])
    native = NativeTestDatabase(settings, Mock(side_effect=[lookup, writer, reader]))
    native.reserve_email()
    with pytest.raises(pytest.fail.Exception, match="verification failed"):
        native.cleanup()
    assert not native.cleanup_verified


def test_tracking_rejects_unreserved_user_and_session_before_connect(settings):
    connect = Mock()
    native = NativeTestDatabase(settings, connect)
    with pytest.raises(TestDatabaseSafetyError):
        native.track_user(42, "unreserved@example.com")
    with pytest.raises(TestDatabaseSafetyError):
        native.track_session(8, 42)
    connect.assert_not_called()


def test_tracking_requires_matching_user_and_session_ownership(settings):
    lookup = connection_with((TEST_DATABASE,), None)
    user = connection_with((TEST_DATABASE,), (42,))
    session = connection_with((TEST_DATABASE,), (8, "synthetic-hash"))
    native = NativeTestDatabase(settings, Mock(side_effect=[lookup, user, session]))
    email = native.reserve_email()
    native.track_user(42, email)
    native.track_session(8, 42)
    assert user.execute.call_args.args[1] == (42, email)
    assert session.execute.call_args.args[1] == (8, 42)


def test_missing_session_schema_stops_without_ddl(settings):
    connection = connection_with(None, [])
    native = NativeTestDatabase(settings, Mock())
    with pytest.raises(pytest.fail.Exception, match="constraints"):
        native._check_session_schema(connection)
    statements = [call.args[0] for call in connection.execute.call_args_list]
    assert all(statement.startswith("SELECT") for statement in statements)


def test_manual_session_guard_rejects_other_accounts_without_writes(settings):
    connection = connection_with((TEST_DATABASE,), (42, "unreserved@example.com"))
    native = NativeTestDatabase(settings, Mock(return_value=connection))
    with pytest.raises(TestDatabaseSafetyError):
        native.require_reserved_session(generate_session_token())
    assert all(call.args[0].startswith("SELECT") for call in connection.execute.call_args_list)


def test_manual_missing_or_unknown_session_does_not_claim_unrelated_records(settings):
    connection = connection_with((TEST_DATABASE,), None)
    connect = Mock(return_value=connection)
    native = NativeTestDatabase(settings, connect)
    native.require_reserved_session(None)
    connect.assert_not_called()
    native.require_reserved_session(generate_session_token())
    assert not native._users
