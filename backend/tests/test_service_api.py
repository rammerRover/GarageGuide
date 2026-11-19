import json
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from itertools import product
from unittest.mock import AsyncMock, Mock

import psycopg
import pytest
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app import authentication, database, service_queries, service_schemas, session_queries
from app.config import AuthConfigurationError
from app.routes import services
from app.schemas import RegistrationResponse
from app.service_schemas import ServiceListResponse, ServiceRecord
from app.vehicle_queries import VehicleNotFoundError
from app.vehicle_schemas import VEHICLE_ID_ERROR
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers


pytestmark = pytest.mark.usefixtures("forbid_database")
NOW = datetime(2026, 11, 18, tzinfo=timezone.utc)
DEADLINE = authentication.SESSION_DEADLINE_HEADER
PRIVATE = "synthetic-private-service-marker"
PATH = "/api/vehicles/123/services"
REAL_LIST = service_queries.list_services
REAL_CREATE = service_queries.create_service


@pytest.fixture
def body(monkeypatch):
    monkeypatch.setattr(service_schemas, "get_current_date", lambda: date(2026, 11, 18))
    return {"service_date": "2020-02-29", "service_type": "maintenance", "description": "Changed oil"}


@pytest.fixture
def queries(monkeypatch):
    actor = session_queries.AuthenticatedSession(
        RegistrationResponse(id=7, email="synthetic@example.com", created_at=NOW), 11, NOW + timedelta(minutes=30),
    )

    def listing(settings, *, actor, vehicle_id, prepare_response):
        result = ServiceListResponse(vehicle_id=vehicle_id, services=[])
        prepare_response(result)
        return result

    def creating(settings, *, actor, vehicle_id, service, prepare_response):
        result = ServiceRecord(id=456, vehicle_id=vehicle_id, created_at=NOW, **dict(service))
        prepare_response(result)
        return result

    mocks = {"session": Mock(return_value=actor), "list": Mock(side_effect=listing), "create": Mock(side_effect=creating)}
    monkeypatch.setattr(session_queries, "validate_and_extend_session", mocks["session"])
    monkeypatch.setattr(service_queries, "list_services", mocks["list"])
    monkeypatch.setattr(service_queries, "create_service", mocks["create"])
    return actor, mocks


def request(client, method, path=PATH, **options):
    if method == "POST":
        options.setdefault("headers", AUTH_HEADERS)
    return client.request(method, path, **options)


def assert_safe(response, status, caplog):
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"
    assert DEADLINE not in response.headers
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    for record in caplog.records:
        if record.name.startswith("app."):
            assert not record.exc_info and not record.args and not record.stack_info


def test_owned_empty_get_uses_trusted_actor_without_mutation_headers(client, queries):
    actor, mocks = queries
    response = client.get(PATH + "?user_id=999&owner_id=999")
    assert response.status_code == 200 and response.json() == {"vehicle_id": 123, "services": []}
    assert response.headers[DEADLINE] == actor.expires_at.isoformat()
    assert response.headers["cache-control"] == "no-store" and "set-cookie" not in response.headers
    assert mocks["list"].call_args.kwargs["actor"] is actor
    assert mocks["list"].call_args.kwargs["vehicle_id"] == 123
    mocks["session"].assert_called_once()


def test_populated_list_returns_exact_public_records(client, queries):
    record = ServiceRecord(id=456, vehicle_id=123, service_date=date(2020, 2, 29), service_type="repair",
                           description="Repair", mileage=None, operating_hours=None, cost=None, notes=None, created_at=NOW)

    def listing(settings, *, actor, vehicle_id, prepare_response):
        result = ServiceListResponse(vehicle_id=vehicle_id, services=[record])
        prepare_response(result)
        return result

    queries[1]["list"].side_effect = listing
    response = client.get(PATH)
    assert response.status_code == 200
    assert response.json() == {"vehicle_id": 123, "services": [record.model_dump(mode="json")]}
    assert response.headers[DEADLINE] == queries[0].expires_at.isoformat()


@pytest.mark.parametrize("mileage,hours,cost", list(product([None, "0.0"], [None, "0.0"], [None, "0.00"])))
@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://127.0.0.1:4173"])
def test_post_exact_public_shape_and_committed_actor_deadline(client, queries, body, mileage, hours, cost, origin):
    actor, mocks = queries
    response = request(client, "POST", PATH + "?user_id=999", json={**body, "mileage": mileage, "operating_hours": hours, "cost": cost},
                       headers={**AUTH_HEADERS, "Origin": origin, "Content-Type": "application/json; charset=utf-8"})
    assert response.status_code == 201
    assert response.json() == {"id": 456, "vehicle_id": 123, **body, "mileage": mileage,
                               "operating_hours": hours, "cost": cost, "notes": None, "created_at": "2026-11-18T00:00:00Z"}
    assert response.headers[DEADLINE] == actor.expires_at.isoformat()
    assert response.headers["cache-control"] == "no-store" and "set-cookie" not in response.headers
    assert mocks["create"].call_args.kwargs["actor"] is actor
    mocks["session"].assert_called_once()


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("raw,expected", [("1", 1), ("2147483647", 2147483647), ("%31%32%33", 123)])
def test_decoded_canonical_id_is_bound_without_browser_ownership(client, queries, body, method, raw, expected):
    response = request(client, method, f"/api/vehicles/{raw}/services", **({"json": body} if method == "POST" else {}))
    assert response.status_code == (201 if method == "POST" else 200)
    assert queries[1]["create" if method == "POST" else "list"].call_args.kwargs["vehicle_id"] == expected


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("raw", ["0", "00", "01", "%30%31", "+1", "-1", "1.0", "1e2", "%201", "1%20", "1%09", "%D9%A1", "%EF%BC%91", "2147483648", "999999999999999999999", PRIVATE])
def test_invalid_id_is_sanitized_without_business_query(client, queries, body, method, raw, caplog):
    response = request(client, method, f"/api/vehicles/{raw}/services", **({"json": body} if method == "POST" else {}))
    assert_safe(response, 422, caplog)
    assert response.json() == {"detail": [{"loc": ["path", "vehicle_id"], "msg": VEHICLE_ID_ERROR, "type": "value_error"}]}
    queries[1]["list"].assert_not_called()
    queries[1]["create"].assert_not_called()


@pytest.mark.parametrize("case", CSRF_CASES)
def test_post_policy_precedes_body_read_authentication_and_business_writes(client, queries, monkeypatch, case, caplog):
    read_body = AsyncMock(side_effect=RuntimeError(PRIVATE))
    monkeypatch.setattr(Request, "body", read_body)
    response = request(client, "POST", content="{" + PRIVATE, headers=csrf_headers(case))
    assert_safe(response, 403, caplog)
    assert response.json() == {"detail": "Request not allowed."}
    read_body.assert_not_awaited()
    assert all(mock.call_count == 0 for mock in queries[1].values())


@pytest.mark.parametrize("changes", [
    {"user_id": PRIVATE}, {"owner_id": PRIVATE}, {"id": PRIVATE}, {"vehicle_id": PRIVATE},
    {"created_at": PRIVATE}, {"total_cost": PRIVATE}, {"parts": PRIVATE}, {PRIVATE: PRIVATE},
    {"password": PRIVATE}, {"description": PRIVATE + "\x00"}, {"notes": PRIVATE + "\ud800"},
    {"service_date": "2099-01-01"}, {"service_date": PRIVATE}, {"service_type": PRIVATE},
    {"mileage": PRIVATE}, {"operating_hours": 0}, {"cost": PRIVATE}, {"cost": "0.001"},
    {"description": None}, {"notes": {PRIVATE: PRIVATE}},
])
def test_invalid_service_body_is_sanitized_without_writes(client, queries, body, changes, caplog):
    response = request(client, "POST", content=json.dumps({**body, **changes}))
    assert_safe(response, 422, caplog)
    assert all(set(entry) == {"loc", "msg", "type"} for entry in response.json()["detail"])
    queries[1]["create"].assert_not_called()


@pytest.mark.parametrize("raw", ["{" + PRIVATE, "null", "[]", "true", '"' + PRIVATE + '"', "{}", ""])
def test_malformed_or_nonobject_or_missing_bodies_are_sanitized(client, queries, raw, caplog):
    response = request(client, "POST", content=raw)
    assert_safe(response, 422, caplog)
    queries[1]["create"].assert_not_called()


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_not_found_has_no_deadline_or_private_details(client, queries, body, method, caplog):
    queries[1]["create" if method == "POST" else "list"].side_effect = VehicleNotFoundError()
    response = request(client, method, **({"json": body} if method == "POST" else {}))
    assert_safe(response, 404, caplog)
    assert response.json() == {"detail": "Vehicle not found."}


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("failure", ["invalid-session", "authentication-db", "authentication-unexpected", "service-db", "driver-db", "unexpected"])
def test_fixed_failure_responses_and_cookie_behavior(client, queries, body, method, failure, caplog):
    client.cookies.set("garageguide_session", PRIVATE)
    mocks = queries[1]
    if failure.startswith("authentication") or failure == "invalid-session":
        mocks["session"].side_effect = {
            "invalid-session": session_queries.InvalidSessionError(),
            "authentication-db": psycopg.OperationalError(PRIVATE),
            "authentication-unexpected": RuntimeError(PRIVATE),
        }[failure]
    else:
        mocks["create" if method == "POST" else "list"].side_effect = {
            "service-db": service_queries.ServiceUnavailableError(),
            "driver-db": psycopg.errors.QueryCanceled(PRIVATE), "unexpected": RuntimeError(PRIVATE),
        }[failure]
    response = request(client, method, **({"json": body} if method == "POST" else {}))
    status = 401 if failure == "invalid-session" else 500 if failure in ("unexpected", "authentication-unexpected") else 503
    assert_safe(response, status, caplog)
    detail = "Not authenticated." if status == 401 else "Internal server error" if status == 500 else (
        "Authentication unavailable. Please try again." if failure == "authentication-db" else "Service history unavailable. Please try again.")
    assert response.json() == {"detail": detail}
    if status == 401:
        assert "max-age=0" in response.headers["set-cookie"].lower()
    else:
        assert "set-cookie" not in response.headers
    if failure.startswith("authentication") or failure == "invalid-session":
        mocks["list"].assert_not_called()
        mocks["create"].assert_not_called()


def test_auth_configuration_failure_is_distinct_and_precedes_business(client, queries, body, monkeypatch, caplog):
    monkeypatch.setattr(authentication, "request_auth_settings", Mock(side_effect=AuthConfigurationError()))
    response = request(client, "POST", json=body)
    assert_safe(response, 503, caplog)
    assert response.json() == {"detail": "Authentication unavailable. Please try again."}
    assert all(mock.call_count == 0 for mock in queries[1].values())


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("failure_at", ["prepare", "missing-prepare", "commit", "close"])
def test_prepared_success_is_not_returned_after_transaction_or_preparation_failure(client, queries, body, monkeypatch, method, failure_at, caplog):
    original = REAL_CREATE if method == "POST" else REAL_LIST
    monkeypatch.setattr(service_queries, "create_service" if method == "POST" else "list_services", original)
    connection = Mock()
    row = (456, 123, date(2020, 2, 29), "maintenance", "Changed oil", None, None, None, None, NOW)
    connection.execute.return_value.fetchone.side_effect = [(123,), row]
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
            if failure_at == "close":
                raise psycopg.InterfaceError(PRIVATE)

    monkeypatch.setattr(database, "connect_database", connect)
    if failure_at == "prepare":
        monkeypatch.setattr(services, "_service_response", Mock(side_effect=RuntimeError(PRIVATE)))
    if failure_at == "missing-prepare":
        monkeypatch.setattr(service_queries, "create_service" if method == "POST" else "list_services", Mock())
    response = request(client, method, **({"json": body} if method == "POST" else {}))
    assert_safe(response, 503 if failure_at in ("commit", "close") else 500, caplog)
    if failure_at != "missing-prepare":
        assert events[-1] == "close"
        if failure_at in ("prepare", "commit"):
            assert events[-2] == "rollback"


def test_real_query_returns_201_only_after_preparation_commit_and_close(client, queries, body, monkeypatch):
    monkeypatch.setattr(service_queries, "create_service", REAL_CREATE)
    connection = Mock()
    connection.execute.return_value.fetchone.side_effect = [(123,), (456, 123, date(2020, 2, 29), "maintenance", "Changed oil", None, None, None, None, NOW)]
    events = []
    original = services._service_response

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
    monkeypatch.setattr(services, "_service_response", prepare)
    response = request(client, "POST", json=body)
    assert response.status_code == 201
    assert events == ["open", "prepared", "commit", "close"]


def test_validation_boundary_drops_arbitrary_locations_types_messages_inputs_and_context(client, queries, body, caplog):
    queries[1]["create"].side_effect = RequestValidationError([
        {"loc": ("body", PRIVATE), "type": PRIVATE, "msg": PRIVATE, "input": PRIVATE, "ctx": {"error": PRIVATE}},
    ])
    response = request(client, "POST", json=body)
    assert_safe(response, 422, caplog)
    assert response.json() == {"detail": [{"loc": ["body"], "msg": "Enter a valid value.", "type": "value_error"}]}


@pytest.mark.parametrize("status", [400, 418])
def test_http_exception_details_are_not_reflected(client, queries, body, status, caplog):
    queries[1]["create"].side_effect = HTTPException(status_code=status, detail=PRIVATE)
    response = request(client, "POST", json=body)
    assert_safe(response, 422 if status == 400 else 500, caplog)


@pytest.mark.parametrize("method,path,status", [
    ("GET", PATH + "/", 307), ("GET", PATH + "/456/unknown", 404), ("POST", PATH + "/456", 405),
    ("PATCH", PATH, 405), ("DELETE", PATH, 405), ("PUT", PATH, 405),
])
def test_unsupported_routes_and_methods_are_not_cacheable(client, method, path, status):
    response = client.request(method, path, follow_redirects=False)
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store" and DEADLINE not in response.headers
