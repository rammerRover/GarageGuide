import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import database
from app.config import AuthSettings, get_auth_settings, get_settings, load_settings
from app.main import create_app
from database_support import NativeTestDatabase


@pytest.fixture
def forbid_database(monkeypatch):
    def unexpected_connection(*args, **kwargs):
        pytest.fail("Credential tests must not connect to PostgreSQL", pytrace=False)

    monkeypatch.setattr(psycopg, "connect", unexpected_connection)


@pytest.fixture(autouse=True)
def native_database(request, monkeypatch):
    if request.node.get_closest_marker("integration") is None:
        return None
    if os.environ.get("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 for the prepared garageguide_app_test database")
    settings = load_settings(testing=True)
    native = NativeTestDatabase(settings, database.connect_database)

    def cleanup():
        try:
            native.cleanup()
            if native.cleanup_verified:
                users, sessions = native.cleanup_counts
                print(
                    f"Verified exact cleanup: {users} synthetic users and {sessions} tracked "
                    f"sessions and {native.cleanup_vehicle_count} vehicles absent from garageguide_app_test."
                )
        except BaseException:
            request.session.shouldstop = "Native cleanup failed; resolve tracked fixtures before continuing"
            raise

    request.addfinalizer(cleanup)
    monkeypatch.setattr(database, "connect_database", native.connect)
    native.check_schema()
    return native


@pytest.fixture
def test_settings():
    # Fail before any connection if environment variables target another database.
    return load_settings(testing=True)


@pytest.fixture
def client(test_settings):
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: test_settings
    application.dependency_overrides[get_auth_settings] = lambda: AuthSettings(
        "testing", False, "http://127.0.0.1:8000"
    )
    with TestClient(application, base_url="http://127.0.0.1:8000") as test_client:
        yield test_client
