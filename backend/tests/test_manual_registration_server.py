from unittest.mock import Mock

import pytest

from app import database, user_queries
from app.config import Settings, get_settings, TEST_DATABASE
from database_support import TestDatabaseSafetyError
import manual_registration_server as manual


pytestmark = pytest.mark.usefixtures("forbid_database")


def test_manual_backend_requires_explicit_opt_in_before_settings(monkeypatch):
    monkeypatch.delenv("RUN_DB_TESTS", raising=False)
    settings = Mock()
    monkeypatch.setattr(manual, "load_settings", settings)
    with pytest.raises(TestDatabaseSafetyError):
        with manual.prepared_test_backend():
            pytest.fail("Unsafe manual backend was exposed")
    settings.assert_not_called()


@pytest.mark.parametrize("target", ["garageguide_app", "postgres", "another_database"])
def test_manual_backend_rejects_unsafe_settings_before_connect(monkeypatch, target):
    monkeypatch.setenv("RUN_DB_TESTS", "1")
    monkeypatch.setenv("PGDATABASE", target)
    with pytest.raises(ValueError, match=TEST_DATABASE):
        with manual.prepared_test_backend():
            pytest.fail("Unsafe manual backend was exposed")


@pytest.fixture
def guarded_setup(monkeypatch):
    monkeypatch.setenv("RUN_DB_TESTS", "1")
    settings = Settings("unused", 5432, TEST_DATABASE, "synthetic", "")
    monkeypatch.setattr(manual, "load_settings", lambda *, testing: settings)
    native = Mock()
    native.reserve_email.side_effect = [f"reserved-{n}@example.com" for n in range(3)]
    monkeypatch.setattr(manual, "NativeTestDatabase", Mock(return_value=native))
    original_connect = Mock()
    original_create = Mock(return_value="synthetic result")
    monkeypatch.setattr(database, "connect_database", original_connect)
    monkeypatch.setattr(user_queries, "create_user", original_create)
    return settings, native, original_connect, original_create


def test_manual_backend_limits_accounts_and_restores_after_failure(guarded_setup):
    settings, native, original_connect, original_create = guarded_setup
    with pytest.raises(RuntimeError, match="Synthetic stop"):
        with manual.prepared_test_backend() as (application, emails):
            assert database.connect_database is native.connect
            assert application.dependency_overrides[get_settings]() is settings
            user_queries.create_user(settings, email=emails[0], password_hash="synthetic hash")
            with pytest.raises(TestDatabaseSafetyError):
                user_queries.create_user(settings, email="unreserved@example.com", password_hash="synthetic hash")
            assert original_create.call_count == 1
            raise RuntimeError("Synthetic stop")
    native.check_schema.assert_called_once()
    native.cleanup.assert_called_once()
    assert database.connect_database is original_connect
    assert user_queries.create_user is original_create


def test_manual_backend_cleanup_runs_when_setup_fails(guarded_setup):
    _, native, original_connect, original_create = guarded_setup
    native.reserve_email.side_effect = RuntimeError("Synthetic setup failure")
    with pytest.raises(RuntimeError, match="setup failure"):
        with manual.prepared_test_backend():
            pytest.fail("Incomplete setup was exposed")
    native.cleanup.assert_called_once()
    assert database.connect_database is original_connect
    assert user_queries.create_user is original_create


def test_manual_launcher_reports_verified_cleanup_without_starting_server(guarded_setup, monkeypatch, capsys):
    _, native, _, _ = guarded_setup
    run = Mock()
    monkeypatch.setattr(manual.uvicorn, "run", run)
    assert manual.main([]) == 0
    native.cleanup.assert_called_once()
    assert run.call_args.kwargs == {"host": "127.0.0.1", "port": 8000, "access_log": False}
    assert "Verified cleanup:" in capsys.readouterr().out


def test_manual_launcher_never_reports_success_when_cleanup_fails(guarded_setup, monkeypatch, capsys):
    _, native, _, _ = guarded_setup
    native.cleanup.side_effect = RuntimeError("Synthetic cleanup failure")
    monkeypatch.setattr(manual.uvicorn, "run", Mock())
    assert manual.main([]) == 1
    captured = capsys.readouterr()
    assert "Verified cleanup:" not in captured.out
    assert "without confirmed cleanup" in captured.err
