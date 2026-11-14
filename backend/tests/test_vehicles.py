import json
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import psycopg
import pytest
from fastapi import Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app import authentication, database, session_queries, vehicle_queries, vehicle_schemas
from app.config import AuthConfigurationError
from app.routes import vehicles
from app.schemas import RegistrationResponse
from app.vehicle_schemas import Vehicle, VehicleListResponse
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers


pytestmark = pytest.mark.usefixtures("forbid_database")
NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)
DEADLINE = authentication.SESSION_DEADLINE_HEADER
PRIVATE = "synthetic-private-vehicle-marker"


@pytest.fixture
def body(monkeypatch):
    monkeypatch.setattr(vehicle_schemas, "get_current_year", lambda: 2026)
    return {"year": 2020, "make": "Honda", "model": "Synthetic", "vehicle_type": "Custom"}


@pytest.fixture
def queries(monkeypatch):
    user = RegistrationResponse(id=7, email="synthetic@example.com", created_at=NOW)
    actor = session_queries.AuthenticatedSession(user, 11, NOW + timedelta(minutes=30))
    mocks = {"session": Mock(return_value=actor), "list": Mock(), "create": Mock()}

    def listing(settings, *, actor, prepare_response):
        result = VehicleListResponse(vehicles=[])
        prepare_response(result)
        return result

    def creating(settings, *, actor, vehicle, prepare_response):
        result = Vehicle(
            id=42, year=vehicle.year, make=vehicle.make, model=vehicle.model,
            vehicle_type=vehicle.vehicle_type, engine=vehicle.engine,
            mileage=vehicle.mileage, operating_hours=vehicle.operating_hours,
            readings_updated_at=NOW if vehicle.mileage is not None or vehicle.operating_hours is not None else None,
            created_at=NOW,
        )
        prepare_response(result)
        return result

    mocks["list"].side_effect = listing
    mocks["create"].side_effect = creating
    monkeypatch.setattr(session_queries, "validate_and_extend_session", mocks["session"])
    monkeypatch.setattr(vehicle_queries, "list_vehicles", mocks["list"])
    monkeypatch.setattr(vehicle_queries, "create_vehicle", mocks["create"])
    return actor, mocks


def assert_error(response, status, detail, caplog):
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert response.headers["cache-control"] == "no-store"
    assert DEADLINE not in response.headers
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert all(record.exc_info is None and not record.args for record in caplog.records)


def test_empty_get_needs_no_mutation_headers(client, queries):
    actor, mocks = queries
    response = client.get("/api/vehicles?user_id=999&owner_id=999")
    assert response.status_code == 200
    assert response.json() == {"vehicles": []}
    assert response.headers[DEADLINE] == actor.expires_at.isoformat()
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in response.headers
    assert mocks["list"].call_args.kwargs["actor"] is actor


@pytest.mark.parametrize(
    ("mileage", "hours"), [(None, None), ("0.0", None), (None, "0.0"), ("12.3", "45.6")],
)
@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://127.0.0.1:4173"])
def test_post_exact_public_shape_and_committed_actor_deadline(client, queries, body, mileage, hours, origin):
    actor, mocks = queries
    response = client.post("/api/vehicles?user_id=999", json={**body, "mileage": mileage, "operating_hours": hours},
                           headers={**AUTH_HEADERS, "Origin": origin, "Content-Type": "application/json; charset=utf-8"})
    assert response.status_code == 201
    assert response.json() == {
        "id": 42, **body, "engine": None, "mileage": mileage, "operating_hours": hours,
        "readings_updated_at": "2026-11-13T00:00:00Z" if mileage is not None or hours is not None else None,
        "created_at": "2026-11-13T00:00:00Z",
    }
    assert response.headers[DEADLINE] == actor.expires_at.isoformat()
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in response.headers
    assert mocks["create"].call_args.kwargs["actor"] is actor


@pytest.mark.parametrize("case", CSRF_CASES)
def test_policy_rejection_precedes_parsing_authentication_and_business_writes(client, queries, caplog, case):
    _, mocks = queries
    response = client.post("/api/vehicles", content="{" + PRIVATE, headers=csrf_headers(case))
    assert_error(response, 403, "Request not allowed.", caplog)
    assert all(mock.call_count == 0 for mock in mocks.values())


@pytest.mark.parametrize("changes", [
    {"user_id": PRIVATE}, {"owner_id": PRIVATE}, {"id": PRIVATE}, {"created_at": PRIVATE},
    {"readings_updated_at": PRIVATE}, {PRIVATE: PRIVATE}, {"password": PRIVATE},
    {"make": "\x00" + PRIVATE}, {"engine": PRIVATE + "\ud800"}, {"model": " "},
    {"vehicle_type": None}, {"mileage": PRIVATE}, {"operating_hours": 0},
    {"year": 1885}, {"year": 2028}, {"year": True}, {"year": PRIVATE},
])
def test_invalid_fields_are_sanitized_before_creation(client, queries, body, changes, caplog):
    _, mocks = queries
    response = client.post("/api/vehicles", content=json.dumps({**body, **changes}), headers=AUTH_HEADERS)
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store" and DEADLINE not in response.headers
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    for entry in response.json()["detail"]:
        assert set(entry) == {"loc", "msg", "type"}
        assert entry["loc"] == ["body"] or entry["loc"] in [["body", field] for field in vehicles._FIELDS]
        assert entry["msg"] in {*vehicles._MESSAGES.values(), *vehicles._FIELD_MESSAGES.values()}
        assert entry["type"] in vehicles._MESSAGES
    mocks["create"].assert_not_called()


@pytest.mark.parametrize("content", ["{", '{"make":"' + PRIVATE, "[]", "null", '"' + PRIVATE + '"', "{}"])
def test_malformed_or_nonobject_body_has_safe_errors(client, queries, content, caplog):
    response = client.post("/api/vehicles", content=content, headers=AUTH_HEADERS)
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store" and DEADLINE not in response.headers
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert all(set(entry) == {"loc", "msg", "type"} for entry in response.json()["detail"])
    queries[1]["create"].assert_not_called()


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("error_type", [session_queries.InvalidSessionError, psycopg.OperationalError,
                                      psycopg.InterfaceError, psycopg.errors.QueryCanceled, RuntimeError])
def test_authentication_errors_preserve_fixed_cookie_and_error_behavior(client, queries, body, caplog, method, error_type):
    _, mocks = queries
    mocks["session"].side_effect = error_type() if error_type is session_queries.InvalidSessionError else error_type(PRIVATE)
    client.cookies.set("garageguide_session", "unusable-synthetic-cookie")
    response = client.request(method, "/api/vehicles", **({"json": body, "headers": AUTH_HEADERS} if method == "POST" else {}))
    status = 401 if error_type is session_queries.InvalidSessionError else 500 if error_type is RuntimeError else 503
    detail = {401: "Not authenticated.", 503: "Authentication unavailable. Please try again.", 500: "Internal server error"}[status]
    assert_error(response, status, detail, caplog)
    if status == 401:
        cookie = response.headers["set-cookie"].lower()
        assert all(part in cookie for part in ["max-age=0", "httponly", "path=/", "samesite=lax"])
    else:
        assert "set-cookie" not in response.headers
        assert client.cookies.get("garageguide_session") is not None
    mocks["list"].assert_not_called()
    mocks["create"].assert_not_called()


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("error_type", [vehicle_queries.VehicleUnavailableError, psycopg.OperationalError,
                                      psycopg.InterfaceError, psycopg.errors.QueryCanceled, RuntimeError])
def test_business_errors_have_no_deadline_or_cookie_change(client, queries, body, caplog, method, error_type):
    _, mocks = queries
    mocks["list" if method == "GET" else "create"].side_effect = (
        error_type() if error_type is vehicle_queries.VehicleUnavailableError else error_type(PRIVATE)
    )
    response = client.request(method, "/api/vehicles", **({"json": body, "headers": AUTH_HEADERS} if method == "POST" else {}))
    status = 500 if error_type is RuntimeError else 503
    assert_error(response, status, "Internal server error" if status == 500 else "Vehicles unavailable. Please try again.", caplog)
    assert "set-cookie" not in response.headers


def test_auth_configuration_failure_is_authentication_503(client, queries, caplog, monkeypatch):
    monkeypatch.setattr(authentication, "request_auth_settings", Mock(side_effect=AuthConfigurationError()))
    response = client.get("/api/vehicles")
    assert_error(response, 503, "Authentication unavailable. Please try again.", caplog)
    queries[1]["list"].assert_not_called()


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("failure_at", ["prepare", "commit", "missing-preparation"])
def test_real_query_prepares_inside_transaction_and_never_returns_failed_success(
    client, queries, body, monkeypatch, caplog, method, failure_at,
):
    real_query = REAL_LIST if method == "GET" else REAL_CREATE
    monkeypatch.setattr(vehicle_queries, "list_vehicles" if method == "GET" else "create_vehicle", real_query)
    connection = Mock()
    row = (42, 2020, "Honda", "Synthetic", None, "Custom", None, None, None, NOW)
    connection.execute.return_value.fetchone.return_value = row
    connection.execute.return_value.fetchall.return_value = [row]
    events = []

    @contextmanager
    def connect(settings, *, read_only):
        events.append("open")
        try:
            yield connection
            events.append("commit")
            if failure_at == "commit":
                raise psycopg.OperationalError(PRIVATE)
        except BaseException:
            events.append("rollback")
            raise
        finally:
            events.append("close")

    monkeypatch.setattr(database, "connect_database", connect)
    if failure_at == "prepare":
        def fail_preparation(*args):
            assert events == ["open"]
            raise RuntimeError(PRIVATE)
        monkeypatch.setattr(vehicles, "_vehicle_response", fail_preparation)
    if failure_at == "missing-preparation":
        monkeypatch.setattr(vehicle_queries, "list_vehicles" if method == "GET" else "create_vehicle", Mock())
    response = client.request(method, "/api/vehicles", **({"json": body, "headers": AUTH_HEADERS} if method == "POST" else {}))
    status = 503 if failure_at == "commit" else 500
    assert_error(response, status, "Vehicles unavailable. Please try again." if status == 503 else "Internal server error", caplog)
    if failure_at != "missing-preparation":
        assert events[-2:] == ["rollback", "close"]


def test_real_creation_commits_and_closes_after_response_preparation(client, queries, body, monkeypatch):
    monkeypatch.setattr(vehicle_queries, "create_vehicle", REAL_CREATE)
    connection = Mock()
    connection.execute.return_value.fetchone.return_value = (42, 2020, "Honda", "Synthetic", None, "Custom", None, None, None, NOW)
    events = []
    original = vehicles._vehicle_response

    def prepare(*args):
        assert events == ["open"]
        response = original(*args)
        events.append("prepared")
        return response

    @contextmanager
    def connect(settings, *, read_only):
        events.append("open")
        yield connection
        events.extend(["commit", "close"])

    monkeypatch.setattr(database, "connect_database", connect)
    monkeypatch.setattr(vehicles, "_vehicle_response", prepare)
    response = client.post("/api/vehicles", json=body, headers=AUTH_HEADERS)
    assert response.status_code == 201
    assert events == ["open", "prepared", "commit", "close"]
    assert response.headers[DEADLINE] == queries[0].expires_at.isoformat()


@pytest.mark.parametrize("status", [200, 201, 401, 403, 422, 500, 503])
def test_reusable_deadline_helper_only_attaches_success(status, queries):
    response = Response(status_code=status)
    authentication.attach_session_deadline(response, queries[0])
    assert (DEADLINE in response.headers) == (status in (200, 201))


def test_reusable_deadline_helper_rejects_naive_deadline(queries):
    actor = session_queries.AuthenticatedSession(queries[0].user, 11, NOW.replace(tzinfo=None))
    response = Response(status_code=200)
    with pytest.raises(ValueError, match="timezone-aware"):
        authentication.attach_session_deadline(response, actor)
    assert DEADLINE not in response.headers


def test_populated_list_has_only_public_fields(client, queries, body):
    vehicle = Vehicle(
        id=42, **body, engine=None, mileage=None, operating_hours=None,
        readings_updated_at=None, created_at=NOW,
    )

    def listing(settings, *, actor, prepare_response):
        result = VehicleListResponse(vehicles=[vehicle])
        prepare_response(result)
        return result

    queries[1]["list"].side_effect = listing
    response = client.get("/api/vehicles")
    assert response.status_code == 200
    assert response.json() == {"vehicles": [vehicle.model_dump(mode="json")]}
    assert response.headers[DEADLINE] == queries[0].expires_at.isoformat()


@pytest.mark.parametrize("status", [400, 418])
def test_http_exception_details_are_not_reflected(client, queries, body, caplog, status):
    queries[1]["create"].side_effect = HTTPException(status_code=status, detail=PRIVATE)
    response = client.post("/api/vehicles", json=body, headers=AUTH_HEADERS)
    assert response.status_code == (422 if status == 400 else 500)
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert response.headers["cache-control"] == "no-store" and DEADLINE not in response.headers


def test_validation_boundary_never_reflects_arbitrary_exception_messages(client, queries, body, caplog):
    queries[1]["create"].side_effect = RequestValidationError([
        {"loc": ("body", PRIVATE), "type": PRIVATE, "msg": PRIVATE, "input": PRIVATE, "ctx": {"error": PRIVATE}},
    ])
    response = client.post("/api/vehicles", json=body, headers=AUTH_HEADERS)
    assert_error(response, 422, [{"loc": ["body"], "type": "value_error", "msg": "Enter a valid value."}], caplog)


@pytest.mark.parametrize(("method", "path", "expected"), [
    ("GET", "/api/vehicles/1", 404), ("PATCH", "/api/vehicles", 405),
    ("DELETE", "/api/vehicles", 405), ("GET", "/api/vehicles/", 307),
])
def test_no_detail_mutations_or_cacheable_routing_responses(client, method, path, expected):
    response = client.request(method, path, follow_redirects=False)
    assert response.status_code == expected
    assert response.headers["cache-control"] == "no-store" and DEADLINE not in response.headers


REAL_LIST = vehicle_queries.list_vehicles
REAL_CREATE = vehicle_queries.create_vehicle
