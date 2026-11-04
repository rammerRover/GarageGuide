from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import psycopg
import pytest

from app import database, user_queries
from app.config import Settings, TEST_DATABASE
from app.user_queries import DuplicateEmailError, create_user
from database_support import NativeTestDatabase, TestDatabaseSafetyError


@pytest.fixture
def settings():
    return Settings("unused", 5432, TEST_DATABASE, "synthetic", "")


@pytest.mark.parametrize("read_only", [True, False], ids=["health-read-only", "writable"])
def test_connection_options_and_timeouts(settings, monkeypatch, read_only):
    connect = Mock()
    monkeypatch.setattr(psycopg, "connect", connect)
    result = database.connect_database(settings, read_only=read_only)
    assert result is connect.return_value
    connect.assert_called_once_with(
        host=settings.host, port=5432, dbname=TEST_DATABASE,
        user=settings.user, password="", connect_timeout=3,
        options=("-c default_transaction_read_only=" + ("on" if read_only else "off")
                 + " -c statement_timeout=3000"),
    )


@pytest.fixture
def transaction(monkeypatch):
    connection = Mock()
    events = []
    commit_error = []

    @contextmanager
    def connect(settings, *, read_only):
        assert read_only is False
        events.append("open")
        try:
            yield connection
            events.append("commit")
            if commit_error:
                raise commit_error[0]
        except BaseException:
            events.append("rollback")
            raise
        finally:
            events.append("close")

    monkeypatch.setattr(database, "connect_database", connect)
    return connection, events, commit_error


def test_parameterized_lookup_insert_and_commit(settings, transaction):
    connection, events, _ = transaction
    row = (7, "a' OR TRUE --@example.com", datetime(2026, 11, 4, tzinfo=timezone.utc))
    connection.execute.side_effect = [Mock(fetchone=lambda: None), Mock(fetchone=lambda: row)]
    result = create_user(settings, email=row[1], password_hash="synthetic-hash")
    assert result == row
    assert events == ["open", "commit", "close"]
    assert connection.execute.call_args_list[0].args == (
        "SELECT id FROM public.users WHERE email = %s", (row[1],)
    )
    assert connection.execute.call_args_list[1].args == (
        "INSERT INTO public.users (email, password_hash) VALUES (%s, %s) "
        "RETURNING id, email, created_at", (row[1], "synthetic-hash")
    )


def test_precheck_duplicate_rolls_back_without_insert(settings, transaction):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.return_value = (7,)
    with pytest.raises(DuplicateEmailError):
        create_user(settings, email="synthetic@example.com", password_hash="synthetic-hash")
    assert connection.execute.call_count == 1
    assert events == ["open", "rollback", "close"]


class UniqueViolationStub(psycopg.errors.UniqueViolation):
    def __init__(self, constraint):
        self.constraint = constraint
        super().__init__("Synthetic constraint failure")

    @property
    def diag(self):
        return SimpleNamespace(constraint_name=self.constraint)


@pytest.mark.parametrize("constraint", ["users_email_key", "another_constraint"])
def test_unique_violation_is_translated_only_after_rollback(settings, transaction, constraint):
    connection, events, _ = transaction
    failure = UniqueViolationStub(constraint)
    connection.execute.side_effect = [Mock(fetchone=lambda: None), failure]
    expected = DuplicateEmailError if constraint == "users_email_key" else UniqueViolationStub
    with pytest.raises(expected):
        create_user(settings, email="synthetic@example.com", password_hash="synthetic-hash")
    assert events == ["open", "rollback", "close"]


@pytest.mark.parametrize("failure_at", ["lookup", "insert", "commit", "missing-return"])
def test_failures_never_return_success_and_close(settings, transaction, failure_at):
    connection, events, commit_error = transaction
    failure = psycopg.OperationalError("Synthetic database failure")
    found = Mock(fetchone=lambda: None)
    inserted = Mock(fetchone=lambda: (7, "synthetic@example.com", datetime.now(timezone.utc)))
    connection.execute.side_effect = [failure] if failure_at == "lookup" else [found, inserted]
    if failure_at == "insert":
        connection.execute.side_effect = [found, failure]
    if failure_at == "commit":
        commit_error.append(failure)
    if failure_at == "missing-return":
        connection.execute.side_effect = [found, found]
    with pytest.raises((psycopg.OperationalError, RuntimeError)):
        create_user(settings, email="synthetic@example.com", password_hash="synthetic-hash")
    assert events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("target", ["garageguide_app", "postgres", "other_test"])
def test_native_settings_guard_prevents_connection(settings, target):
    connect = Mock()
    native = NativeTestDatabase(settings, connect)
    unsafe = Settings("unused", 5432, target, "synthetic", "")
    with pytest.raises(TestDatabaseSafetyError):
        native.connect(unsafe)
    connect.assert_not_called()


@pytest.mark.parametrize("actual", ["garageguide_app", "postgres", "other_test"])
def test_actual_database_guard_closes_without_writes(settings, actual):
    connection = Mock()
    connection.execute.return_value.fetchone.return_value = (actual,)
    native = NativeTestDatabase(settings, Mock(return_value=connection))
    with pytest.raises(TestDatabaseSafetyError):
        native.connect(settings)
    connection.execute.assert_called_once_with("SELECT current_database()")
    connection.close.assert_called_once()


@pytest.mark.parametrize("driver_failure", [False, True], ids=["unexpected-error", "driver-error"])
def test_failed_database_name_query_closes_without_writes(settings, driver_failure):
    connection = Mock()
    error = psycopg.OperationalError if driver_failure else RuntimeError
    connection.execute.side_effect = error("Synthetic name-check failure")
    native = NativeTestDatabase(settings, Mock(return_value=connection))
    expected = pytest.fail.Exception if driver_failure else RuntimeError
    with pytest.raises(expected):
        native.connect(settings)
    connection.execute.assert_called_once_with("SELECT current_database()")
    connection.close.assert_called_once()


def test_actual_database_checked_once_per_new_connection(settings):
    first, second = Mock(), Mock()
    for connection in (first, second):
        connection.execute.return_value.fetchone.return_value = (TEST_DATABASE,)
    native = NativeTestDatabase(settings, Mock(side_effect=[first, second]))
    for _ in range(2):
        connection = native.connect(settings)
        connection.execute("INSERT synthetic", (1,))
        connection.execute("DELETE synthetic", (1,))
    for connection in (first, second):
        assert [call.args[0] for call in connection.execute.call_args_list] == [
            "SELECT current_database()", "INSERT synthetic", "DELETE synthetic"
        ]


def test_health_uses_read_only_connection(settings, monkeypatch):
    connect = MagicMock()
    connection = connect.return_value.__enter__.return_value
    connection.execute.side_effect = [
        Mock(fetchone=lambda: (1,)),
        Mock(fetchall=lambda: [(name,) for name in database.EXPECTED_TABLES]),
        Mock(fetchone=lambda: (True,)),
    ]
    monkeypatch.setattr(database, "connect_database", connect)
    assert database.check_database(settings)
    connect.assert_called_once_with(settings, read_only=True)


def test_cleanup_targets_only_reserved_email_and_recovered_id(settings):
    lookup, writer, reader = MagicMock(), MagicMock(), MagicMock()
    lookup.execute.side_effect = [
        Mock(fetchone=lambda: (TEST_DATABASE,)), Mock(fetchone=lambda: None)
    ]
    writer.execute.side_effect = [
        Mock(fetchone=lambda: (TEST_DATABASE,)), Mock(fetchone=lambda: (42,)), Mock()
    ]
    reader.execute.side_effect = [
        Mock(fetchone=lambda: (TEST_DATABASE,)), Mock(fetchall=lambda: [])
    ]
    for connection in (lookup, writer, reader):
        connection.__enter__.return_value = connection
    connect = Mock(side_effect=[lookup, writer, reader])
    native = NativeTestDatabase(settings, connect)
    email = native.reserve_email()
    native.cleanup()
    assert writer.execute.call_args_list[-1].args == (
        "DELETE FROM public.users WHERE id = %s AND email = %s", (42, email)
    )
    assert reader.execute.call_args_list[-1].args == (
        "SELECT id FROM public.users WHERE email = ANY(%s)", ([email],)
    )
    native.cleanup()
    assert connect.call_count == 3


def test_fixture_collision_is_never_claimed_or_deleted(settings):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.execute.side_effect = [
        Mock(fetchone=lambda: (TEST_DATABASE,)), Mock(fetchone=lambda: (42,))
    ]
    connect = Mock(return_value=connection)
    native = NativeTestDatabase(settings, connect)
    with pytest.raises(pytest.fail.Exception, match="collision"):
        native.reserve_email()
    native.cleanup()
    assert connect.call_count == 1
    assert connection.execute.call_count == 2


def test_cleanup_connection_cannot_write_to_wrong_actual_database(settings):
    lookup, unsafe = MagicMock(), Mock()
    lookup.__enter__.return_value = lookup
    lookup.execute.side_effect = [
        Mock(fetchone=lambda: (TEST_DATABASE,)), Mock(fetchone=lambda: None)
    ]
    unsafe.execute.return_value.fetchone.return_value = ("postgres",)
    native = NativeTestDatabase(settings, Mock(side_effect=[lookup, unsafe]))
    native.reserve_email()
    with pytest.raises(TestDatabaseSafetyError):
        native.cleanup()
    unsafe.execute.assert_called_once_with("SELECT current_database()")
    unsafe.close.assert_called_once()
