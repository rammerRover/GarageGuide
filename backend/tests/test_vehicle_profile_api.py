import json
from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import Mock

import psycopg
import pytest
from fastapi.exceptions import RequestValidationError

from app import authentication, database, session_queries, vehicle_queries
from app.config import AuthConfigurationError
from app.routes import vehicles
from app.vehicle_schemas import (
    CONFIRMATION_ERROR, EMPTY_PATCH_ERROR, REQUIRED_PATCH_ERROR, VEHICLE_ID_ERROR,
    ReadingConfirmationRequired, Vehicle, VehiclePatch,
)
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers
from test_vehicle_profile_queries import arrange, stored_row
from test_vehicle_queries import transaction
from test_vehicles import DEADLINE, PRIVATE, assert_error, queries


pytestmark = pytest.mark.usefixtures("forbid_database")
REAL_GET = vehicle_queries.get_vehicle
REAL_UPDATE = vehicle_queries.update_vehicle


def call(client, method, path="/api/vehicles/42", **options):
    return client.request(method, path, **({"json": {"model": "Changed"}, "headers": AUTH_HEADERS} if method == "PATCH" else {}), **options)


@pytest.fixture
def profile_queries(queries, monkeypatch):
    actor, mocks = queries
    current = Vehicle.model_validate(dict(zip(vehicle_queries.PUBLIC_FIELDS, stored_row(), strict=True)))

    def get(settings, *, actor, vehicle_id, prepare_response):
        result = Vehicle.model_validate({**dict(current), "id": vehicle_id})
        prepare_response(result)
        return result

    def update(settings, *, actor, vehicle_id, patch, prepare_response):
        result = Vehicle.model_validate({**dict(current), **patch.changes(), "id": vehicle_id})
        prepare_response(result)
        return result

    mocks["detail"] = Mock(side_effect=get)
    mocks["update"] = Mock(side_effect=update)
    monkeypatch.setattr(vehicle_queries, "get_vehicle", mocks["detail"])
    monkeypatch.setattr(vehicle_queries, "update_vehicle", mocks["update"])
    return actor, mocks, current


@pytest.mark.parametrize("method", ["GET", "PATCH"])
@pytest.mark.parametrize("path,expected", [("1", 1), ("2147483647", 2147483647), ("%34%32", 42)])
def test_decoded_canonical_id_and_trusted_actor_are_passed_once(client, profile_queries, method, path, expected):
    actor, mocks, current = profile_queries
    response = call(client, method, "/api/vehicles/" + path + "?user_id=999&owner_id=999")
    public = current.model_dump(mode="json")
    public["id"] = expected
    if method == "PATCH":
        public["model"] = "Changed"
    assert response.status_code == 200 and response.json() == public
    assert response.headers["cache-control"] == "no-store" and response.headers[DEADLINE] == actor.expires_at.isoformat()
    assert "set-cookie" not in response.headers
    query = mocks["detail" if method == "GET" else "update"]
    assert query.call_args.kwargs["actor"] is actor and query.call_args.kwargs["vehicle_id"] == expected
    mocks["session"].assert_called_once()


@pytest.mark.parametrize("method", ["GET", "PATCH"])
@pytest.mark.parametrize("raw", ["0", "00", "01", "%30%31", "+1", "-1", "1.0", "1e2", "%201", "1%20", "1%09", "%D9%A1", "%EF%BC%91", "2147483648", "999999999999999999999", PRIVATE])
def test_bad_id_has_one_exact_sanitized_path_error(client, profile_queries, caplog, method, raw):
    response = call(client, method, "/api/vehicles/" + raw)
    assert_error(response, 422, [{"loc": ["path", "vehicle_id"], "msg": VEHICLE_ID_ERROR, "type": "value_error"}], caplog)
    profile_queries[1]["detail"].assert_not_called()
    profile_queries[1]["update"].assert_not_called()


@pytest.mark.parametrize("case", CSRF_CASES)
def test_patch_policy_precedes_body_parsing_auth_and_business_calls(client, profile_queries, caplog, case):
    response = client.patch("/api/vehicles/42", content="{" + PRIVATE, headers=csrf_headers(case))
    assert_error(response, 403, "Request not allowed.", caplog)
    assert all(mock.call_count == 0 for mock in profile_queries[1].values())


@pytest.mark.parametrize("name", ["Origin", "Content-Type", "X-GarageGuide-CSRF"])
def test_empty_policy_headers_reject_even_before_id_validation(client, profile_queries, caplog, name):
    response = client.patch("/api/vehicles/01", content="{" + PRIVATE, headers={**AUTH_HEADERS, name: ""})
    assert_error(response, 403, "Request not allowed.", caplog)
    assert all(mock.call_count == 0 for mock in profile_queries[1].values())


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://127.0.0.1:4173"])
def test_patch_accepts_json_charset_with_trusted_origins(client, profile_queries, origin):
    response = client.patch("/api/vehicles/42", json={"engine": None}, headers={**AUTH_HEADERS, "Origin": origin, "Content-Type": "application/json; charset=utf-8"})
    assert response.status_code == 200 and response.json()["engine"] is None


@pytest.mark.parametrize("body,location,message", [
    ({}, ["body"], EMPTY_PATCH_ERROR),
    ({"reading_confirmation": {}}, ["body"], EMPTY_PATCH_ERROR),
    *[({name: None}, ["body", name], REQUIRED_PATCH_ERROR) for name in ["year", "make", "model", "vehicle_type"]],
    ({"mileage": "9", "reading_confirmation": None}, ["body", "reading_confirmation"], CONFIRMATION_ERROR),
    ({"mileage": "9", "reading_confirmation": []}, ["body", "reading_confirmation"], CONFIRMATION_ERROR),
    ({"mileage": "9", "reading_confirmation": {PRIVATE: PRIVATE}}, ["body", "reading_confirmation"], CONFIRMATION_ERROR),
    ({"mileage": "9", "reading_confirmation": {"mileage": PRIVATE}}, ["body", "reading_confirmation"], CONFIRMATION_ERROR),
    ({"mileage": "9", "reading_confirmation": {"mileage": None}}, ["body", "reading_confirmation"], CONFIRMATION_ERROR),
    ({"make": "Honda", "reading_confirmation": {"mileage": "10"}}, ["body", "reading_confirmation"], CONFIRMATION_ERROR),
])
def test_exact_empty_null_and_confirmation_errors(client, profile_queries, caplog, body, location, message):
    response = client.patch("/api/vehicles/42", json=body, headers=AUTH_HEADERS)
    assert_error(response, 422, [{"loc": location, "msg": message, "type": "value_error"}], caplog)
    profile_queries[1]["update"].assert_not_called()


@pytest.mark.parametrize("body", [
    {"user_id": PRIVATE}, {"owner_id": PRIVATE}, {"id": PRIVATE}, {"created_at": PRIVATE},
    {"readings_updated_at": PRIVATE}, {PRIVATE: PRIVATE}, {"make": PRIVATE + "\x00"},
    {"engine": PRIVATE + "\ud800"}, {"mileage": PRIVATE}, {"operating_hours": 0},
    {"year": True}, {"year": 1885}, {"year": "2020"},
])
def test_invalid_patch_values_and_extra_fields_never_escape(client, profile_queries, caplog, body):
    response = client.patch("/api/vehicles/42", content=json.dumps(body), headers=AUTH_HEADERS)
    assert response.status_code == 422 and response.headers["cache-control"] == "no-store"
    assert DEADLINE not in response.headers and PRIVATE not in response.text + caplog.text
    for item in response.json()["detail"]:
        assert set(item) == {"loc", "msg", "type"}
        assert item["loc"] == ["body"] or item["loc"] in [["body", field] for field in vehicles._FIELDS]
    profile_queries[1]["update"].assert_not_called()


@pytest.mark.parametrize("content", ["{", '{"model":"' + PRIVATE, "[]", "null", '"' + PRIVATE + '"', b"\xff"])
def test_malformed_or_nonobject_patch_is_safe(client, profile_queries, caplog, content):
    response = client.patch("/api/vehicles/42", content=content, headers=AUTH_HEADERS)
    assert response.status_code == 422 and PRIVATE not in response.text + caplog.text
    assert response.headers["cache-control"] == "no-store" and DEADLINE not in response.headers
    assert all(set(item) == {"loc", "msg", "type"} for item in response.json()["detail"])
    profile_queries[1]["update"].assert_not_called()


@pytest.mark.parametrize("method", ["GET", "PATCH"])
def test_missing_and_foreign_share_fixed_not_found_boundary(client, profile_queries, caplog, method):
    query = profile_queries[1]["detail" if method == "GET" else "update"]
    query.side_effect = vehicle_queries.VehicleNotFoundError()
    first = call(client, method, "/api/vehicles/42")
    second = call(client, method, "/api/vehicles/43")
    assert_error(first, 404, "Vehicle not found.", caplog)
    assert first.content == second.content and dict(first.headers) == dict(second.headers)


@pytest.mark.parametrize("method", ["GET", "PATCH"])
@pytest.mark.parametrize("error_type", [session_queries.InvalidSessionError, psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled, RuntimeError])
def test_auth_failures_retain_existing_status_and_cookie_policy(client, profile_queries, caplog, method, error_type):
    mocks = profile_queries[1]
    mocks["session"].side_effect = error_type() if error_type is session_queries.InvalidSessionError else error_type(PRIVATE)
    client.cookies.set("garageguide_session", "synthetic-unusable-cookie")
    response = call(client, method)
    status = 401 if error_type is session_queries.InvalidSessionError else 500 if error_type is RuntimeError else 503
    assert_error(response, status, {401: "Not authenticated.", 503: "Authentication unavailable. Please try again.", 500: "Internal server error"}[status], caplog)
    if status == 401:
        cookie = response.headers["set-cookie"].lower()
        assert all(part in cookie for part in ["max-age=0", "httponly", "path=/", "samesite=lax"])
    else:
        assert "set-cookie" not in response.headers and client.cookies.get("garageguide_session") is not None
    mocks["detail"].assert_not_called()
    mocks["update"].assert_not_called()


@pytest.mark.parametrize("method", ["GET", "PATCH"])
@pytest.mark.parametrize("error_type", [vehicle_queries.VehicleUnavailableError, psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled, RuntimeError])
def test_vehicle_failures_do_not_attach_deadline_or_change_cookie(client, profile_queries, caplog, method, error_type):
    query = profile_queries[1]["detail" if method == "GET" else "update"]
    query.side_effect = error_type() if error_type is vehicle_queries.VehicleUnavailableError else error_type(PRIVATE)
    response = call(client, method)
    status = 500 if error_type is RuntimeError else 503
    assert_error(response, status, "Internal server error" if status == 500 else "Vehicles unavailable. Please try again.", caplog)
    assert "set-cookie" not in response.headers


def test_auth_configuration_failure_stays_authentication_503(client, profile_queries, caplog, monkeypatch):
    monkeypatch.setattr(authentication, "request_auth_settings", Mock(side_effect=AuthConfigurationError()))
    assert_error(client.get("/api/vehicles/42"), 503, "Authentication unavailable. Please try again.", caplog)
    profile_queries[1]["detail"].assert_not_called()


@pytest.mark.parametrize("fields", [(), ("mileage",), ("mileage", "operating_hours")])
def test_409_has_exact_restricted_shape_and_no_deadline(client, profile_queries, caplog, fields):
    values = {name: "1000.0" for name in fields}
    profile_queries[1]["update"].side_effect = ReadingConfirmationRequired(fields, values)
    response = call(client, "PATCH")
    assert response.status_code == 409
    assert response.json() == {"detail": "Reading changes require confirmation.", "fields": list(fields), "current_readings": values}
    assert response.headers["cache-control"] == "no-store" and DEADLINE not in response.headers
    assert "set-cookie" not in response.headers and PRIVATE not in caplog.text


@pytest.mark.parametrize("fields,values", [((PRIVATE,), {PRIVATE: PRIVATE}), (("mileage",), {"mileage": PRIVATE}), (("mileage",), {"mileage": "1.0", "owner_id": PRIVATE}), (("operating_hours", "mileage"), {"mileage": "1.0", "operating_hours": "2.0"})])
def test_malformed_confirmation_outcome_is_generic_500_not_private_error(client, profile_queries, caplog, fields, values):
    profile_queries[1]["update"].side_effect = ReadingConfirmationRequired(fields, values)
    assert_error(call(client, "PATCH"), 500, "Internal server error", caplog)


def test_raw_validation_exception_data_and_context_are_never_reflected(client, profile_queries, caplog):
    profile_queries[1]["update"].side_effect = RequestValidationError([
        {"loc": ("body", PRIVATE), "msg": PRIVATE, "type": PRIVATE, "input": PRIVATE, "ctx": {"error": PRIVATE}},
    ])
    assert_error(call(client, "PATCH"), 422, [{"loc": ["body"], "msg": "Enter a valid value.", "type": "value_error"}], caplog)


def test_real_confirmation_exchange_is_atomic_and_returns_only_after_commit(client, profile_queries, transaction, monkeypatch):
    connection, events, _ = transaction
    monkeypatch.setattr(vehicle_queries, "update_vehicle", REAL_UPDATE)
    changed = stored_row(mileage=Decimal("900"))
    connection.execute.side_effect = [Mock(fetchone=lambda: stored_row()), Mock(fetchone=lambda: stored_row()), Mock(fetchone=lambda: changed)]
    denied = client.patch("/api/vehicles/42", json={"mileage": "900"}, headers=AUTH_HEADERS)
    assert denied.status_code == 409 and denied.json()["current_readings"] == {"mileage": "1000.0"}
    assert events[-2:] == ["rollback", "close"]
    saved = client.patch("/api/vehicles/42", json={"mileage": "900", "reading_confirmation": {"mileage": "1000"}}, headers=AUTH_HEADERS)
    assert saved.status_code == 200 and saved.json()["mileage"] == "900.0"
    assert set(saved.json()) == set(vehicle_queries.PUBLIC_FIELDS)
    assert events[-2:] == ["commit", "close"]
    assert saved.headers[DEADLINE] == profile_queries[0].expires_at.isoformat()


@pytest.mark.parametrize("current,fields", [("1200", ["mileage"]), ("800", []), ("900", []), (None, [])])
def test_real_stale_confirmation_never_writes_even_when_no_decrease_remains(client, profile_queries, transaction, monkeypatch, caplog, current, fields):
    connection, events, _ = transaction
    monkeypatch.setattr(vehicle_queries, "update_vehicle", REAL_UPDATE)
    connection.execute.return_value.fetchone.return_value = stored_row(mileage=None if current is None else Decimal(current))
    response = client.patch("/api/vehicles/42", json={"model": PRIVATE, "mileage": "900", "reading_confirmation": {"mileage": "1000"}}, headers=AUTH_HEADERS)
    assert response.status_code == 409 and response.json()["fields"] == fields
    assert response.json()["current_readings"] == ({"mileage": "1200.0"} if fields else {})
    assert connection.execute.call_count == 1 and events[-2:] == ["rollback", "close"]
    assert PRIVATE not in response.text + caplog.text and DEADLINE not in response.headers


def test_real_two_reading_rejection_does_not_save_other_fields(client, profile_queries, transaction, monkeypatch):
    connection, events, _ = transaction
    monkeypatch.setattr(vehicle_queries, "update_vehicle", REAL_UPDATE)
    connection.execute.return_value.fetchone.return_value = stored_row()
    response = client.patch("/api/vehicles/42", json={"model": "Do not apply", "mileage": None, "operating_hours": "9", "reading_confirmation": {"mileage": "1000"}}, headers=AUTH_HEADERS)
    assert response.status_code == 409 and response.json()["fields"] == ["mileage", "operating_hours"]
    assert connection.execute.call_count == 1 and events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("method", ["GET", "PATCH"])
@pytest.mark.parametrize("phase", ["success", "prepare", "serialize", "query", "commit", "close", "invalid-return", "missing-preparation"])
def test_real_query_response_and_transaction_failures_never_release_failed_success(client, profile_queries, transaction, monkeypatch, caplog, method, phase):
    connection, events, commit_errors = transaction
    name = "get_vehicle" if method == "GET" else "update_vehicle"
    monkeypatch.setattr(vehicle_queries, name, REAL_GET if method == "GET" else REAL_UPDATE)
    arrange(connection, VehiclePatch(model="Changed"))
    if phase == "prepare":
        monkeypatch.setattr(vehicles, "_vehicle_response", Mock(side_effect=RuntimeError(PRIVATE)))
    elif phase == "serialize":
        monkeypatch.setattr(Vehicle, "model_dump", Mock(side_effect=RuntimeError(PRIVATE)))
    elif phase == "query":
        connection.execute.side_effect = psycopg.OperationalError(PRIVATE)
    elif phase == "commit":
        commit_errors.append(psycopg.OperationalError(PRIVATE))
    elif phase == "close":
        original = database.connect_database

        @contextmanager
        def closed_then_lost(settings, *, read_only):
            with original(settings, read_only=read_only) as opened:
                yield opened
            raise psycopg.OperationalError(PRIVATE)

        monkeypatch.setattr(database, "connect_database", closed_then_lost)
    elif phase == "invalid-return":
        connection.execute.side_effect = [Mock(fetchone=lambda: stored_row(year=0))]
    elif phase == "missing-preparation":
        monkeypatch.setattr(vehicle_queries, name, Mock())
    response = call(client, method)
    if phase == "success":
        assert response.status_code == 200 and events[-2:] == ["commit", "close"]
        assert response.headers[DEADLINE] == profile_queries[0].expires_at.isoformat()
    else:
        status = 503 if phase in ["query", "commit", "close"] else 500
        assert_error(response, status, "Vehicles unavailable. Please try again." if status == 503 else "Internal server error", caplog)
        if phase != "missing-preparation":
            assert events[-1] == "close"


@pytest.mark.parametrize("method,path,status", [("PUT", "/api/vehicles/42", 405), ("DELETE", "/api/vehicles/42", 405), ("GET", "/api/vehicles/42/extra", 404), ("GET", "/api/vehicles/42/", 307)])
def test_detail_routing_failures_are_not_cacheable(client, method, path, status):
    response = client.request(method, path, follow_redirects=False)
    assert response.status_code == status and response.headers["cache-control"] == "no-store"
    assert DEADLINE not in response.headers
