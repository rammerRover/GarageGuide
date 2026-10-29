import os

import psycopg
import pytest

from app.config import load_settings
from app.routes import health


def test_api_health_does_not_need_database(client, monkeypatch):
    def unexpected_call(*args, **kwargs):
        pytest.fail("API liveness must not connect to PostgreSQL")

    monkeypatch.setattr(psycopg, "connect", unexpected_call)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_failure_is_generic(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise psycopg.OperationalError("private connection details")

    monkeypatch.setattr(psycopg, "connect", unavailable)
    response = client.get("/api/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "private" not in response.text


def test_missing_schema_and_successful_retry(client, monkeypatch):
    monkeypatch.setattr(health, "check_database", lambda settings: False)
    response = client.get("/api/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database schema unavailable"}
    monkeypatch.setattr(health, "check_database", lambda settings: True)
    response = client.get("/api/health/db")
    assert response.status_code == 200
    assert response.json()["schema"] == "ready"


@pytest.mark.parametrize("database", ["garageguide_app", "postgres", "other_test"])
def test_tests_reject_other_databases(monkeypatch, database):
    monkeypatch.setenv("PGDATABASE", database)
    with pytest.raises(ValueError, match="garageguide_app_test"):
        load_settings(testing=True)


@pytest.mark.integration
def test_real_database_health(client):
    if os.environ.get("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 after preparing garageguide_app_test")
    response = client.get("/api/health/db")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "ok", "database": "connected", "schema": "ready",
    }
