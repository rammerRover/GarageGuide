import json
from datetime import date
from unittest.mock import AsyncMock, Mock

import psycopg
import pytest
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app import authentication, service_queries, session_queries
from app.routes import services
from app.service_schemas import (
    EMPTY_PATCH_ERROR, REMOVAL_ERROR, REQUIRED_PATCH_ERROR, SERVICE_ID_ERROR,
    ServiceRecord, ServiceRemovalResponse,
)
from app.vehicle_schemas import VEHICLE_ID_ERROR
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers
from test_service_api import DEADLINE, NOW, PRIVATE, assert_safe, body, queries
from test_service_queries import row, service, transaction


pytestmark = pytest.mark.usefixtures("forbid_database")
PATH = "/api/vehicles/123/services/456"
REAL = {"GET": service_queries.get_service, "PATCH": service_queries.update_service, "DELETE": service_queries.remove_service}
NAMES = {"GET": "get_service", "PATCH": "update_service", "DELETE": "remove_service"}


@pytest.fixture
def record_queries(queries, monkeypatch):
    actor, mocks = queries
    current = ServiceRecord(id=456, vehicle_id=123, service_date=date(2020, 2, 29), service_type="maintenance",
                            description="Changed oil", mileage=None, operating_hours=None, cost=None, notes=None, created_at=NOW)
    def get(settings, *, actor, vehicle_id, service_id, prepare_response):
        result = ServiceRecord(**{**dict(current), "id": service_id, "vehicle_id": vehicle_id})
        prepare_response(result)
        return result
    def update(settings, *, actor, vehicle_id, service_id, patch, prepare_response):
        result = ServiceRecord(**{**dict(current), **patch.changes(), "id": service_id, "vehicle_id": vehicle_id})
        prepare_response(result)
        return result
    def remove(settings, *, actor, vehicle_id, service_id, confirmation, prepare_response):
        assert confirmation.confirm_removal is True
        result = ServiceRemovalResponse(id=service_id, vehicle_id=vehicle_id, deleted=True)
        prepare_response(result)
        return result
    for method, implementation in (("GET", get), ("PATCH", update), ("DELETE", remove)):
        mocks[method] = Mock(side_effect=implementation)
        monkeypatch.setattr(service_queries, NAMES[method], mocks[method])
    return actor, mocks, current


def call(client, method, path=PATH, **options):
    if method != "GET":
        options.setdefault("headers", AUTH_HEADERS)
        if not any(key in options for key in ("json", "content")):
            options["json"] = {"notes": "Corrected notes"} if method == "PATCH" else {"confirm_removal": True}
    return client.request(method, path, **options)


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
def test_exact_success_shapes_actor_scoping_and_success_deadline(client, record_queries, method):
    actor, mocks, current = record_queries
    response = call(client, method, PATH + "?user_id=999&owner_id=999")
    expected = current.model_dump(mode="json")
    if method == "PATCH":
        expected["notes"] = "Corrected notes"
    elif method == "DELETE":
        expected = {"id": 456, "vehicle_id": 123, "deleted": True}
    assert response.status_code == 200 and response.json() == expected
    assert response.headers["cache-control"] == "no-store" and response.headers[DEADLINE] == actor.expires_at.isoformat()
    assert "set-cookie" not in response.headers
    assert mocks[method].call_args.kwargs["actor"] is actor
    assert mocks[method].call_args.kwargs["vehicle_id"] == 123
    assert mocks[method].call_args.kwargs["service_id"] == 456
    mocks["session"].assert_called_once()


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.parametrize("vehicle_id,service_id", [("1", "2147483647"), ("%31%32%33", "%34%35%36")])
def test_both_decoded_ids_use_canonical_validation(client, record_queries, method, vehicle_id, service_id):
    response = call(client, method, f"/api/vehicles/{vehicle_id}/services/{service_id}")
    assert response.status_code == 200
    assert record_queries[1][method].call_args.kwargs["vehicle_id"] == (1 if vehicle_id == "1" else 123)
    assert record_queries[1][method].call_args.kwargs["service_id"] == (2147483647 if service_id == "2147483647" else 456)


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.parametrize("field", ["vehicle_id", "service_id"])
@pytest.mark.parametrize("raw", ["0", "01", "+1", "-1", "1.0", "1e2", "%201", "1%20", "%D9%A1", "2147483648", PRIVATE])
def test_invalid_ids_are_fixed_sanitized_path_errors_without_queries(client, record_queries, method, field, raw, caplog):
    vehicle_id, service_id = (raw, "456") if field == "vehicle_id" else ("123", raw)
    response = call(client, method, f"/api/vehicles/{vehicle_id}/services/{service_id}")
    assert_safe(response, 422, caplog)
    assert response.json() == {"detail": [{"loc": ["path", field], "msg": VEHICLE_ID_ERROR if field == "vehicle_id" else SERVICE_ID_ERROR, "type": "value_error"}]}
    for operation in ("GET", "PATCH", "DELETE"):
        record_queries[1][operation].assert_not_called()


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
@pytest.mark.parametrize("case", CSRF_CASES)
def test_mutation_policy_precedes_body_read_ids_authentication_and_business(client, record_queries, method, case, monkeypatch, caplog):
    reader = AsyncMock(side_effect=RuntimeError(PRIVATE))
    monkeypatch.setattr(Request, "body", reader)
    response = call(client, method, "/api/vehicles/01/services/00", content="{" + PRIVATE, headers=csrf_headers(case))
    assert_safe(response, 403, caplog)
    assert response.json() == {"detail": "Request not allowed."}
    reader.assert_not_awaited()
    assert all(mock.call_count == 0 for mock in record_queries[1].values())


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://127.0.0.1:4173"])
def test_mutations_accept_trusted_origins_and_json_charset(client, record_queries, method, origin):
    assert call(client, method, headers={**AUTH_HEADERS, "Origin": origin, "Content-Type": "application/json; charset=utf-8"}).status_code == 200


@pytest.mark.parametrize("value", [False, None, 0, 1, 1.0, "true", "True", "1", [], {}])
def test_delete_confirmation_is_strict_true_without_coercion(client, record_queries, value, caplog):
    response = call(client, "DELETE", json={"confirm_removal": value})
    assert_safe(response, 422, caplog)
    assert response.json() == {"detail": [{"loc": ["body", "confirm_removal"], "msg": REMOVAL_ERROR, "type": "value_error"}]}
    record_queries[1]["DELETE"].assert_not_called()


@pytest.mark.parametrize("payload", [{}, {"force": True}, {"confirm_removal": True, "force": True},
                                      {"confirm_removal": True, "notes": PRIVATE}, {"confirm_removal": True, PRIVATE: PRIVATE}])
def test_delete_rejects_missing_confirmation_and_any_extra_fields(client, record_queries, payload, caplog):
    response = call(client, "DELETE", json=payload)
    assert_safe(response, 422, caplog)
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
    record_queries[1]["DELETE"].assert_not_called()


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
@pytest.mark.parametrize("raw", ["{" + PRIVATE, "null", "[]", '"' + PRIVATE + '"', "true", ""])
def test_mutation_bodies_must_be_valid_json_objects(client, record_queries, method, raw, caplog):
    response = call(client, method, content=raw)
    assert_safe(response, 422, caplog)
    record_queries[1][method].assert_not_called()


def test_empty_patch_uses_fixed_root_error(client, record_queries, caplog):
    response = call(client, "PATCH", json={})
    assert_safe(response, 422, caplog)
    assert response.json() == {"detail": [{"loc": ["body"], "msg": EMPTY_PATCH_ERROR, "type": "value_error"}]}


@pytest.mark.parametrize("field", ["service_date", "service_type", "description"])
def test_patch_required_fields_cannot_be_cleared(client, record_queries, field, caplog):
    response = call(client, "PATCH", json={field: None})
    assert_safe(response, 422, caplog)
    assert response.json() == {"detail": [{"loc": ["body", field], "msg": REQUIRED_PATCH_ERROR, "type": "value_error"}]}


@pytest.mark.parametrize("payload", [{"notes": None}, {"notes": " "}, {"mileage": None, "operating_hours": "0", "cost": "0"},
                                      {"service_type": "diagnostic"}, {"description": "Changed oil"}])
def test_partial_patch_null_zero_and_equal_values_use_existing_schema(client, record_queries, payload):
    response = call(client, "PATCH", json=payload)
    assert response.status_code == 200
    patch = record_queries[1]["PATCH"].call_args.kwargs["patch"]
    assert patch.model_fields_set == set(payload)
    if "cost" in payload:
        assert response.json()["cost"] == "0.00" and response.json()["operating_hours"] == "0.0"


@pytest.mark.parametrize("payload", [{"user_id": PRIVATE}, {"vehicle_id": PRIVATE}, {"id": PRIVATE},
                                      {"created_at": PRIVATE}, {"reading_confirmation": {"mileage": PRIVATE}},
                                      {"notes": PRIVATE + "\x00"}, {"cost": 0.01}, {"cost": PRIVATE},
                                      {"service_date": PRIVATE}, {"confirm_removal": True}])
def test_patch_errors_never_echo_raw_values_or_metadata(client, record_queries, payload, caplog):
    response = call(client, "PATCH", content=json.dumps(payload))
    assert_safe(response, 422, caplog)
    record_queries[1]["PATCH"].assert_not_called()


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
def test_individual_not_found_uses_one_fixed_404_without_deadline(client, record_queries, method, caplog):
    record_queries[1][method].side_effect = service_queries.ServiceNotFoundError()
    response = call(client, method)
    assert_safe(response, 404, caplog)
    assert response.json() == {"detail": "Service record not found."}


@pytest.mark.parametrize("method,error,message", [
    ("PATCH", service_queries.ServiceEditBlockedError, "Service record is linked to maintenance completion and cannot be changed."),
    ("DELETE", service_queries.ServiceRemovalBlockedError, "Service record has linked data and cannot be removed."),
])
def test_linked_conflicts_have_exact_restricted_409_bodies(client, record_queries, method, error, message, caplog):
    record_queries[1][method].side_effect = error()
    response = call(client, method)
    assert_safe(response, 409, caplog)
    assert response.json() == {"detail": message} and "set-cookie" not in response.headers


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.parametrize("failure", ["invalid", "authentication", "business", "unexpected"])
def test_failures_preserve_cookie_policy_and_safe_errors(client, record_queries, method, failure, caplog):
    mocks = record_queries[1]
    client.cookies.set("garageguide_session", PRIVATE)
    if failure in ("invalid", "authentication"):
        mocks["session"].side_effect = session_queries.InvalidSessionError() if failure == "invalid" else psycopg.OperationalError(PRIVATE)
    else:
        mocks[method].side_effect = service_queries.ServiceUnavailableError() if failure == "business" else RuntimeError(PRIVATE)
    response = call(client, method)
    status = 401 if failure == "invalid" else 500 if failure == "unexpected" else 503
    assert_safe(response, status, caplog)
    detail = {"invalid": "Not authenticated.", "authentication": "Authentication unavailable. Please try again.",
              "business": "Service history unavailable. Please try again.", "unexpected": "Internal server error"}[failure]
    assert response.json() == {"detail": detail}
    if status == 401:
        assert "max-age=0" in response.headers["set-cookie"].lower()
    else:
        assert "set-cookie" not in response.headers
    if failure in ("invalid", "authentication"):
        mocks[method].assert_not_called()


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.parametrize("failure_at", [None, "prepare", "missing-prepare", "commit", "close"])
def test_real_queries_prepare_in_transaction_and_discard_success_after_failures(client, record_queries, transaction, monkeypatch, method, failure_at, caplog):
    connection, events, failures = transaction
    current = record_queries[2]
    row = tuple(getattr(current, name) for name in service_queries.PUBLIC_FIELDS)
    rows = [row]
    if method != "GET":
        rows += [(False, False), (456, 123) if method == "DELETE" else (*row[:8], "Corrected notes", row[9])]
    connection.execute.return_value.fetchone.side_effect = rows
    monkeypatch.setattr(service_queries, NAMES[method], REAL[method])
    original = services._service_response
    def prepare(*args):
        assert events == [("open", method == "GET")]
        if failure_at == "prepare":
            raise RuntimeError(PRIVATE)
        result = original(*args)
        events.append("prepared")
        return result
    monkeypatch.setattr(services, "_service_response", prepare)
    if failure_at in ("commit", "close"):
        failures[failure_at] = psycopg.OperationalError(PRIVATE)
    if failure_at == "missing-prepare":
        monkeypatch.setattr(service_queries, NAMES[method], Mock())
    response = call(client, method)
    if failure_at is None:
        assert response.status_code == 200 and events[-3:] == ["prepared", "commit", "close"]
    else:
        assert_safe(response, 503 if failure_at in ("commit", "close") else 500, caplog)
        if failure_at != "missing-prepare":
            assert events[-1] == "close"


def test_arbitrary_delete_validation_metadata_is_not_reflected(client, record_queries, caplog):
    record_queries[1]["DELETE"].side_effect = RequestValidationError([
        {"loc": ("body", PRIVATE), "msg": PRIVATE, "type": PRIVATE, "input": PRIVATE, "ctx": {"error": PRIVATE}},
    ])
    response = call(client, "DELETE")
    assert_safe(response, 422, caplog)
    assert response.json() == {"detail": [{"loc": ["body"], "msg": "Enter a valid value.", "type": "value_error"}]}


@pytest.mark.parametrize("method,path,status", [("PUT", PATH, 405), ("POST", PATH, 405),
                                              ("GET", PATH + "/", 307), ("GET", PATH + "/unknown", 404)])
def test_unsupported_methods_and_routing_errors_remain_no_store(client, method, path, status):
    response = client.request(method, path, follow_redirects=False)
    assert response.status_code == status and response.headers["cache-control"] == "no-store"
    assert DEADLINE not in response.headers
