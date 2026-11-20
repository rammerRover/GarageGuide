from unittest.mock import AsyncMock, Mock

import psycopg
import pytest
from starlette.requests import Request

from app import authentication, database, service_part_queries as part_queries, session_queries
from app.routes import service_parts
from app.service_part_schemas import (
    CatalogPartPreview, ServicePartListResponse, ServicePartRemovalResponse, ServicePartSnapshot,
)
from app.service_queries import ServiceNotFoundError
from app.vehicle_queries import VehicleNotFoundError
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers
from test_service_api import DEADLINE, PRIVATE, assert_safe, queries
from test_service_part_queries import transaction


pytestmark = pytest.mark.usefixtures("forbid_database")
PATH = "/api/vehicles/123/services/456/parts"
CATALOG = {"id": 22, "manufacturer": "Maker", "part_number": "EX-123", "name": "Catalog filter", "category": "Filters"}
PART = {"id": 789, "service_record_id": 456, "part_id": None, "name": "Manual filter",
        "part_number": None, "manufacturer": None, "quantity": 1, "notes": None}
NAMES = {"list": "list_service_parts", "lookup": "lookup_catalog_part", "add": "attach_service_part", "remove": "remove_service_part"}
REAL = {op: getattr(part_queries, name) for op, name in NAMES.items()}


@pytest.fixture
def parts(queries, monkeypatch):
    actor, previous = queries
    def listing(settings, *, vehicle_id, service_id, prepare_response, **kwargs):
        result = ServicePartListResponse(vehicle_id=vehicle_id, service_record_id=service_id, parts=[])
        prepare_response(result)
        return result
    def lookup(settings, *, lookup, prepare_response, **kwargs):
        result = CatalogPartPreview(**{**CATALOG, **lookup.model_dump()})
        prepare_response(result)
        return result
    def adding(settings, *, service_id, part, prepare_response, **kwargs):
        fields = {"part_id": part.preview.id, "name": part.preview.name, "part_number": part.preview.part_number,
                  "manufacturer": part.preview.manufacturer} if part.source == "catalog" else {
                      field: getattr(part, field) for field in ("name", "part_number", "manufacturer")}
        result = ServicePartSnapshot(**{**PART, **fields, "service_record_id": service_id, "quantity": part.quantity, "notes": part.notes})
        prepare_response(result)
        return result
    def removing(settings, *, snapshot_id, service_id, confirmation, prepare_response, **kwargs):
        assert confirmation.confirm_removal is True
        result = ServicePartRemovalResponse(id=snapshot_id, service_record_id=service_id, deleted=True)
        prepare_response(result)
        return result
    mocks = {}
    for op, function in [("list", listing), ("lookup", lookup), ("add", adding), ("remove", removing)]:
        mocks[op] = Mock(side_effect=function)
        monkeypatch.setattr(part_queries, NAMES[op], mocks[op])
    return actor, mocks, previous["session"]


def call(client, operation, path=PATH, **options):
    method = {"list": "GET", "lookup": "POST", "add": "POST", "remove": "DELETE"}[operation]
    path += "/lookup" if operation == "lookup" else "/789" if operation == "remove" else ""
    if method != "GET":
        options.setdefault("headers", AUTH_HEADERS)
        if "json" not in options and "content" not in options:
            options["json"] = {"manufacturer": "Maker", "part_number": "EX-123"} if operation == "lookup" else {
                "source": "manual", "name": "Manual filter"} if operation == "add" else {"confirm_removal": True}
    return client.request(method, path, **options)


@pytest.mark.parametrize("operation", NAMES)
def test_success_exact_shapes_scoped_actor_and_committed_deadline(client, parts, operation):
    actor, mocks, session = parts
    response = call(client, operation)
    expected = {"vehicle_id": 123, "service_record_id": 456, "parts": []} if operation == "list" else CATALOG if operation == "lookup" else PART if operation == "add" else {"id": 789, "service_record_id": 456, "deleted": True}
    assert response.status_code == (201 if operation == "add" else 200)
    assert response.json() == expected
    assert response.headers["cache-control"] == "no-store" and response.headers[DEADLINE] == actor.expires_at.isoformat()
    assert "set-cookie" not in response.headers
    kwargs = mocks[operation].call_args.kwargs
    assert kwargs["actor"] is actor and kwargs["vehicle_id"] == 123 and kwargs["service_id"] == 456
    session.assert_called_once()


def test_catalog_add_uses_discriminated_model_and_preserves_preview(client, parts):
    response = call(client, "add", json={"source": "catalog", "preview": CATALOG, "notes": " \ufeffnote\ufeff "})
    assert response.status_code == 201 and response.json() == {
        **PART, "part_id": 22, "name": CATALOG["name"], "manufacturer": "Maker", "part_number": "EX-123", "notes": "\ufeffnote\ufeff",
    }
    assert parts[1]["add"].call_args.kwargs["part"].preview.model_dump() == CATALOG


@pytest.mark.parametrize("operation", ["lookup", "add", "remove"])
@pytest.mark.parametrize("case", CSRF_CASES)
def test_mutation_policy_rejects_before_body_or_business_work(client, parts, operation, case, monkeypatch, caplog):
    reader = AsyncMock(side_effect=AssertionError("Body must not be parsed"))
    monkeypatch.setattr(Request, "json", reader)
    response = call(client, operation, content="{" + PRIVATE, headers=csrf_headers(case))
    assert_safe(response, 403, caplog)
    assert response.json() == {"detail": "Request not allowed."}
    reader.assert_not_awaited()
    assert all(mock.call_count == 0 for mock in parts[1].values())


@pytest.mark.parametrize("operation", ["lookup", "add", "remove"])
@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://127.0.0.1:4173"])
def test_json_charset_and_trusted_origins(client, parts, operation, origin):
    response = call(client, operation, headers={**AUTH_HEADERS, "Origin": origin, "Content-Type": "application/json; charset=utf-8"})
    assert response.status_code == (201 if operation == "add" else 200)


@pytest.mark.parametrize("operation", NAMES)
@pytest.mark.parametrize("raw", ["0", "01", "+1", "-1", "1.0", "2147483648", "nonnumeric", "%EF%BC%91"])
@pytest.mark.parametrize("field", ["vehicle_id", "service_id"])
def test_invalid_decoded_parent_ids_are_sanitized(client, parts, operation, raw, field, caplog):
    path = PATH.replace("123" if field == "vehicle_id" else "456", raw)
    response = call(client, operation, path)
    assert_safe(response, 422, caplog)
    assert all(entry["loc"] == ["path", field] and set(entry) == {"loc", "msg", "type"} for entry in response.json()["detail"])
    assert all(mock.call_count == 0 for mock in parts[1].values())


@pytest.mark.parametrize("raw", ["0", "01", "+1", "-1", "1.0", "2147483648", "%EF%BC%91"])
def test_snapshot_ids_are_validated_before_coercion(client, parts, raw, caplog):
    response = client.request("DELETE", PATH + "/" + raw, json={"confirm_removal": True}, headers=AUTH_HEADERS)
    assert_safe(response, 422, caplog)
    assert response.json()["detail"][0]["loc"] == ["path", "snapshot_id"]
    parts[1]["remove"].assert_not_called()


@pytest.mark.parametrize("operation", ["lookup", "add", "remove"])
@pytest.mark.parametrize("raw", ["{", "[]", "null", '"text"', "true", ""])
def test_invalid_json_objects_are_redacted(client, parts, operation, raw, caplog):
    response = call(client, operation, content=raw)
    assert_safe(response, 422, caplog)
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
    parts[1][operation].assert_not_called()


@pytest.mark.parametrize("body", [
    {}, {"source": PRIVATE, "name": PRIVATE}, {"source": "manual", "name": PRIVATE, "user_id": 7},
    {"source": "manual", "name": PRIVATE, PRIVATE: PRIVATE},
    {"source": "manual", "name": PRIVATE, "quantity": True},
    {"source": "catalog", "preview": {**CATALOG, "id": PRIVATE}},
    {"source": "catalog", "preview": {**CATALOG, PRIVATE: PRIVATE}},
    {"source": "catalog", "preview": {**CATALOG, "name": PRIVATE + "\0"}},
])
def test_union_and_nested_preview_validation_never_echo_raw_input(client, parts, body, caplog):
    response = call(client, "add", json=body)
    assert_safe(response, 422, caplog)
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
    parts[1]["add"].assert_not_called()


@pytest.mark.parametrize("confirmation", [None, False, 1, "true", {}, []])
def test_delete_requires_literal_true(client, parts, confirmation, caplog):
    response = call(client, "remove", json={"confirm_removal": confirmation})
    assert_safe(response, 422, caplog)
    parts[1]["remove"].assert_not_called()


@pytest.mark.parametrize("error,operation,status", [
    (VehicleNotFoundError, "list", 404), (ServiceNotFoundError, "list", 404),
    (part_queries.ServicePartNotFoundError, "remove", 404),
    (part_queries.CatalogPartNotFoundError, "lookup", 404),
    (part_queries.CatalogPreviewConflictError, "add", 409),
    (part_queries.ServicePartsUnavailableError, "list", 503),
])
def test_fixed_business_errors_have_no_deadline_or_cookie(client, parts, error, operation, status, caplog):
    parts[1][operation].side_effect = error()
    response = call(client, operation)
    assert_safe(response, status, caplog)
    assert response.json() == {"detail": str(error())}
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("operation", NAMES)
@pytest.mark.parametrize("stage", ["session", "business", "unexpected"])
def test_503_categories_and_unexpected_failures_are_fixed_and_private(client, parts, operation, stage, caplog):
    if stage == "session":
        parts[2].side_effect = psycopg.OperationalError(PRIVATE)
    else:
        parts[1][operation].side_effect = RuntimeError(PRIVATE) if stage == "unexpected" else psycopg.OperationalError(PRIVATE)
    response = call(client, operation)
    assert_safe(response, 500 if stage == "unexpected" else 503, caplog)
    assert response.json() == {"detail": "Internal server error" if stage == "unexpected" else
        "Authentication unavailable. Please try again." if stage == "session" else "Service parts unavailable. Please try again."}
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("operation", NAMES)
def test_invalid_session_clears_cookie_without_business_query(client, parts, operation, caplog):
    parts[2].side_effect = session_queries.InvalidSessionError()
    response = call(client, operation)
    assert_safe(response, 401, caplog)
    assert response.json() == {"detail": "Not authenticated."}
    assert 'garageguide_session=""' in response.headers["set-cookie"]
    parts[1][operation].assert_not_called()


@pytest.mark.parametrize("operation", NAMES)
def test_missing_response_preparation_cannot_be_success(client, parts, operation, caplog):
    parts[1][operation].side_effect = lambda *args, **kwargs: None
    assert_safe(call(client, operation), 500, caplog)


@pytest.mark.parametrize("stage", ["success", "commit", "close", "prepare"])
def test_real_query_boundary_never_returns_uncommitted_prepared_success(client, parts, transaction, stage, monkeypatch, caplog):
    connection, events, failures, _, configure = transaction
    configure("manual")
    monkeypatch.setattr(part_queries, "attach_service_part", REAL["add"])
    if stage in ("commit", "close"):
        failures[stage] = psycopg.OperationalError(PRIVATE)
    if stage == "prepare":
        monkeypatch.setattr(authentication, "attach_session_deadline", Mock(side_effect=RuntimeError(PRIVATE)))
    response = call(client, "add")
    if stage == "success":
        assert response.status_code == 201
    else:
        assert_safe(response, 500 if stage == "prepare" else 503, caplog)
    assert events[-1] == "close"
    assert len([event for event in events if isinstance(event, tuple)]) == 1


def test_routing_errors_and_redirects_are_no_store(client, parts):
    for response in [client.patch(PATH, headers=AUTH_HEADERS), client.get(PATH + "/789"),
                     client.get(PATH + "/", follow_redirects=False)]:
        assert response.status_code in (404, 405, 307)
        assert response.headers["cache-control"] == "no-store" and DEADLINE not in response.headers
