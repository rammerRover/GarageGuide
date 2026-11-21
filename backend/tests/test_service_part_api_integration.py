import json
from contextlib import contextmanager

import psycopg
import pytest

from app import authentication, database, service_part_queries as queries, service_queries, session_queries
from app.service_part_schemas import ServicePartRemovalRequest
from app.service_schemas import ServiceRemovalRequest
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers
from test_service_api_integration import assert_headers
from test_service_part_queries_integration import (
    attach, catalog_request, create_catalog, listing, manual, parent_state, removal,
)
from test_service_queries_integration import create_owned_service, owned_vehicle, reserved_service
from test_service_record_api_integration import owned_api
from test_vehicles_integration import accounts, install


pytestmark = pytest.mark.integration
PRIVATE = "synthetic-private-snapshot-marker"
NAMES = {"list": "list_service_parts", "lookup": "lookup_catalog_part", "add": "attach_service_part", "remove": "remove_service_part"}


def path(vehicle, service):
    return f"/api/vehicles/{vehicle.id}/services/{service.id}/parts"


def call(client, operation, address, *, body=None, snapshot_id=None, headers=None):
    if operation == "list":
        return client.get(address)
    # Raw content preserves deliberately missing/duplicate policy headers;
    # TestClient's json= convenience would synthesize Content-Type.
    options = {"content": json.dumps(body), "headers": AUTH_HEADERS if headers is None else headers}
    if operation == "lookup":
        return client.post(address + "/lookup", **options)
    if operation == "remove":
        options["content"] = json.dumps({"confirm_removal": True} if body is None else body)
        return client.request("DELETE", address + f"/{snapshot_id}", **options)
    return client.post(address, **options)


def test_native_manual_catalog_list_confirmed_removal_and_service_link_protection(client, native_database, accounts, owned_api):
    first = accounts[0]
    actor = first.session
    vehicle, record = owned_api
    before = parent_state(native_database, actor, vehicle, record)
    install(client, first)
    address = path(vehicle, record)
    empty = client.get(address)
    assert_headers(empty, 200, native_database, first)
    assert empty.json() == {"vehicle_id": vehicle.id, "service_record_id": record.id, "parts": []}
    request = manual(native_database, actor, vehicle, record, quantity=2147483647, notes="\ufeffHistorical\ufeff")
    one = client.post(address, json=request.model_dump(), headers=AUTH_HEADERS)
    native_database.remember_part_snapshot(one.json()["id"], record.id, vehicle.id, actor.user.id, request.name)
    assert_headers(one, 201, native_database, first)
    native_database.track_part_snapshot(one.json()["id"], record.id, vehicle.id, actor.user.id, request.name)
    assert one.json()["part_id"] is None and one.json()["quantity"] == 2147483647
    catalog = create_catalog(native_database)
    found = client.post(address + "/lookup", json={"manufacturer": catalog.manufacturer, "part_number": catalog.part_number}, headers=AUTH_HEADERS)
    assert_headers(found, 200, native_database, first)
    assert found.json() == catalog.model_dump(mode="json")
    catalog_body = catalog_request(native_database, actor, vehicle, record, catalog).model_dump()
    del catalog_body["quantity"]
    two = client.post(address, json=catalog_body, headers=AUTH_HEADERS)
    native_database.remember_part_snapshot(two.json()["id"], record.id, vehicle.id, actor.user.id, catalog.name)
    assert_headers(two, 201, native_database, first)
    native_database.track_part_snapshot(two.json()["id"], record.id, vehicle.id, actor.user.id, catalog.name)
    assert two.json()["quantity"] == 1 and two.json()["part_id"] == catalog.id
    collection = client.get(address)
    assert_headers(collection, 200, native_database, first)
    assert collection.json()["parts"] == [one.json(), two.json()]
    blocked = client.request("DELETE", address.removesuffix("/parts"), json={"confirm_removal": True}, headers=AUTH_HEADERS)
    assert_headers(blocked, 409)
    assert blocked.json() == {"detail": "Service record has linked data and cannot be removed."}
    for saved in [one.json(), two.json()]:
        removed = client.request("DELETE", address + f"/{saved['id']}", json={"confirm_removal": True}, headers=AUTH_HEADERS)
        assert_headers(removed, 200, native_database, first)
        assert removed.json() == {"id": saved["id"], "service_record_id": record.id, "deleted": True}
        repeated = client.request("DELETE", address + f"/{saved['id']}", json={"confirm_removal": True}, headers=AUTH_HEADERS)
        assert_headers(repeated, 404)
        assert repeated.json() == {"detail": "Part snapshot not found."}
    assert parent_state(native_database, actor, vehicle, record) == before
    with native_database.connect(native_database.settings, read_only=True) as connection:
        assert connection.execute("SELECT id FROM public.parts WHERE id = %s", (catalog.id,)).fetchone() == (catalog.id,)


@pytest.mark.parametrize("failed_write", ["manual", "catalog"])
def test_native_response_id_survives_later_assertion_and_exact_cleanup(client, native_database, accounts, owned_api, monkeypatch, failed_write):
    original_headers = assert_headers
    acknowledged = 0
    expected = 1 if failed_write == "manual" else 2
    def later_assertion(response, *args, **kwargs):
        nonlocal acknowledged
        original_headers(response, *args, **kwargs)
        if response.status_code == 201:
            acknowledged += 1
            if acknowledged == expected:
                raise AssertionError("Synthetic later header assertion")
    with monkeypatch.context() as changes:
        changes.setitem(globals(), "assert_headers", later_assertion)
        with pytest.raises(AssertionError, match="Synthetic later header assertion"):
            test_native_manual_catalog_list_confirmed_removal_and_service_link_protection(
                client, native_database, accounts, owned_api)
    assert acknowledged == len(native_database._parts) == expected
    native_database.cleanup()
    assert native_database.cleanup_verified
    assert native_database.cleanup_link_counts[0] == expected


@pytest.mark.parametrize("change", ["name", "category", "delete", "replace"])
def test_native_reviewed_preview_conflicts_are_fixed_and_leave_no_attachment(client, native_database, accounts, owned_api, change):
    first = accounts[0]
    vehicle, record = owned_api
    catalog = create_catalog(native_database)
    request = catalog_request(native_database, first.session, vehicle, record, catalog)
    before = parent_state(native_database, first.session, vehicle, record)
    replacement = None
    with native_database.connect(native_database.settings) as connection:
        if change in ("delete", "replace"):
            connection.execute("DELETE FROM public.parts WHERE id = %s", (catalog.id,))
            if change == "replace":
                replacement = connection.execute(
                    "INSERT INTO public.parts (manufacturer, part_number, name, category) VALUES (%s, %s, %s, %s) RETURNING id",
                    (catalog.manufacturer, catalog.part_number, catalog.name, catalog.category),
                ).fetchone()[0]
                native_database.remember_catalog_part(replacement, catalog.manufacturer, catalog.part_number)
        else:
            connection.execute(f"UPDATE public.parts SET {change} = %s WHERE id = %s", (getattr(catalog, change) + " changed", catalog.id))
    if replacement is not None:
        native_database.track_catalog_part(replacement, catalog.manufacturer, catalog.part_number)
    install(client, first)
    response = client.post(path(vehicle, record), json=request.model_dump(), headers=AUTH_HEADERS)
    assert_headers(response, 409)
    assert response.json() == {"detail": "Catalog part changed or is no longer available. Look it up again or enter the part manually."}
    assert listing(native_database, first.session, vehicle, record).parts == []
    assert parent_state(native_database, first.session, vehicle, record) == before


def test_native_catalog_miss_and_deleted_reference_preserve_public_snapshot(client, native_database, accounts, owned_api):
    first = accounts[0]
    vehicle, record = owned_api
    catalog = create_catalog(native_database)
    saved = attach(native_database, first.session, vehicle, record,
                   catalog_request(native_database, first.session, vehicle, record, catalog))
    with native_database.connect(native_database.settings) as connection:
        connection.execute("DELETE FROM public.parts WHERE id = %s", (catalog.id,))
    install(client, first)
    response = client.get(path(vehicle, record))
    assert_headers(response, 200, native_database, first)
    assert response.json()["parts"] == [{**saved.model_dump(mode="json"), "part_id": None}]
    missed = client.post(path(vehicle, record) + "/lookup", json={"manufacturer": catalog.manufacturer, "part_number": catalog.part_number}, headers=AUTH_HEADERS)
    assert_headers(missed, 404)
    assert missed.json() == {"detail": "Catalog part not found. Look it up again or enter the part manually."}


@pytest.mark.parametrize("operation", NAMES)
def test_native_foreign_wrong_parent_and_missing_service_are_indistinguishable(client, native_database, accounts, owned_api, operation):
    first, second = accounts
    vehicle, record = owned_api
    foreign_vehicle = owned_vehicle(native_database, second.session)
    foreign = create_owned_service(native_database, second.session, foreign_vehicle,
        reserved_service(native_database, second.session, foreign_vehicle))
    missing = create_owned_service(native_database, first.session, vehicle,
        reserved_service(native_database, first.session, vehicle))
    service_queries.remove_service(native_database.settings, actor=first.session, vehicle_id=vehicle.id,
        service_id=missing.id, confirmation=ServiceRemovalRequest(confirm_removal=True))
    other_vehicle = owned_vehicle(native_database, first.session)
    request = manual(native_database, first.session, vehicle, record)
    install(client, first)
    body = request.model_dump() if operation == "add" else {"manufacturer": "not-a-real-catalog-maker", "part_number": "synthetic-miss"}
    responses = [call(client, operation, address, body=body if operation in ("add", "lookup") else None, snapshot_id=1) for address in [
        f"/api/vehicles/{vehicle.id}/services/{missing.id}/parts",
        f"/api/vehicles/{vehicle.id}/services/{foreign.id}/parts",
        f"/api/vehicles/{other_vehicle.id}/services/{record.id}/parts",
    ]]
    for response in responses:
        assert_headers(response, 404)
        assert response.json() == {"detail": "Service record not found."}
    assert listing(native_database, first.session, vehicle, record).parts == []
    assert listing(native_database, second.session, foreign_vehicle, foreign).parts == []


@pytest.mark.parametrize("operation", ["lookup", "add", "remove"])
@pytest.mark.parametrize("case", CSRF_CASES)
def test_native_policy_rejection_happens_without_snapshot_or_session_writes(client, native_database, accounts, owned_api, operation, case):
    first = accounts[0]
    vehicle, record = owned_api
    request = manual(native_database, first.session, vehicle, record)
    before = parent_state(native_database, first.session, vehicle, record)
    from test_vehicles_integration import stored_deadline
    deadline = stored_deadline(native_database, first)
    install(client, first)
    response = call(client, operation, path(vehicle, record), body=request.model_dump(), snapshot_id=1, headers=csrf_headers(case))
    assert_headers(response, 403)
    assert response.json() == {"detail": "Request not allowed."}
    assert listing(native_database, first.session, vehicle, record).parts == []
    assert parent_state(native_database, first.session, vehicle, record) == before
    assert stored_deadline(native_database, first) == deadline


@pytest.mark.parametrize("operation", ["add", "remove"])
@pytest.mark.parametrize("failure", ["prepare", "pre-commit", "lost-ack", "authentication"])
def test_native_failure_boundary_rolls_back_or_preserves_uncertain_commit_without_retry(client, native_database, accounts, owned_api, operation, failure, monkeypatch, caplog):
    first = accounts[0]
    vehicle, record = owned_api
    request = manual(native_database, first.session, vehicle, record)
    original = attach(native_database, first.session, vehicle, record, request) if operation == "remove" else None
    query = getattr(queries, NAMES[operation])
    opened = []
    @contextmanager
    def faulty(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection
            if failure == "pre-commit":
                raise psycopg.OperationalError(PRIVATE)
        if failure == "lost-ack":
            raise psycopg.OperationalError(PRIVATE)
    def wrapped(settings, **kwargs):
        if operation == "add":
            prepare_response = kwargs["prepare_response"]
            def prepare(result):
                native_database.remember_part_snapshot(result.id, record.id, vehicle.id, first.session.user.id, result.name)
                prepare_response(result)
            kwargs["prepare_response"] = prepare
        with monkeypatch.context() as patches:
            patches.setattr(database, "connect_database", faulty)
            return query(settings, **kwargs)
    install(client, first)
    with monkeypatch.context() as patches:
        patches.setattr(queries, NAMES[operation], wrapped)
        if failure == "prepare":
            def fail(*args):
                raise RuntimeError(PRIVATE)
            patches.setattr(authentication, "attach_session_deadline", fail)
        if failure == "authentication":
            def fail(*args):
                raise psycopg.OperationalError(PRIVATE)
            patches.setattr(session_queries, "validate_and_extend_session", fail)
        response = call(client, operation, path(vehicle, record), body=request.model_dump() if operation == "add" else None,
                        snapshot_id=original.id if original else None)
    assert_headers(response, 500 if failure == "prepare" else 503)
    assert response.json() == {"detail": "Internal server error" if failure == "prepare" else
        "Authentication unavailable. Please try again." if failure == "authentication" else "Service parts unavailable. Please try again."}
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert "set-cookie" not in response.headers
    assert len(opened) == (0 if failure == "authentication" else 1) and all(connection.closed for connection in opened)
    count = len(listing(native_database, first.session, vehicle, record).parts)
    assert count == (int(failure != "lost-ack") if operation == "remove" else int(failure == "lost-ack"))


@pytest.mark.parametrize("operation", NAMES)
def test_native_missing_session_is_401_with_cookie_deletion_and_no_snapshot_changes(client, native_database, accounts, owned_api, operation):
    first = accounts[0]
    vehicle, record = owned_api
    request = manual(native_database, first.session, vehicle, record)
    client.cookies.clear()
    response = call(client, operation, path(vehicle, record), body=request.model_dump(), snapshot_id=1)
    assert_headers(response, 401)
    assert response.json() == {"detail": "Not authenticated."}
    assert 'garageguide_session=""' in response.headers["set-cookie"]
    assert listing(native_database, first.session, vehicle, record).parts == []


@pytest.mark.parametrize("body", [
    {"source": "manual", "name": PRIVATE, "quantity": True},
    {"source": "manual", "name": PRIVATE, "owner_id": 1},
    {"source": PRIVATE, "name": PRIVATE},
])
def test_native_sanitized_invalid_bodies_write_nothing(client, native_database, accounts, owned_api, body):
    first = accounts[0]
    vehicle, record = owned_api
    install(client, first)
    response = client.post(path(vehicle, record), json=body, headers=AUTH_HEADERS)
    assert_headers(response, 422)
    assert PRIVATE not in response.text
    assert all(set(entry) == {"loc", "msg", "type"} for entry in response.json()["detail"])
    assert listing(native_database, first.session, vehicle, record).parts == []
