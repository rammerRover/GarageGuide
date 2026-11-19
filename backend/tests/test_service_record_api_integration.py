import json
from contextlib import contextmanager
from itertools import product

import psycopg
import pytest

from app import database, service_queries, session_queries
from app.routes import services
from app.service_schemas import ServiceCreate, ServiceRemovalRequest
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers
from test_service_api_integration import PRIVATE, assert_headers, parent, payload
from test_service_record_queries_integration import add_link, snapshot
from test_vehicles_integration import accounts, install, stored_deadline


pytestmark = pytest.mark.integration
NAMES = {"GET": "get_service", "PATCH": "update_service", "DELETE": "remove_service"}


@pytest.fixture
def owned_api(native_database, accounts):
    first = accounts[0]
    vehicle = parent(native_database, first)
    body = payload(native_database, first, vehicle, mileage="500.0", operating_hours="5.0", cost="42.50", notes="Original notes")
    record = service_queries.create_service(native_database.settings, actor=first.session, vehicle_id=vehicle.id, service=ServiceCreate(**body))
    native_database.track_service(record.id, vehicle.id, first.session.user.id, ServiceCreate(**body))
    return vehicle, record


def path(vehicle, record):
    return f"/api/vehicles/{vehicle.id}/services/{record.id}"


def call(client, method, vehicle, record, body=None):
    options = {}
    if method != "GET":
        options = {"content": json.dumps(body if body is not None else (
            {"notes": "Corrected notes"} if method == "PATCH" else {"confirm_removal": True})), "headers": AUTH_HEADERS}
    return client.request(method, path(vehicle, record), **options)


def test_native_get_patch_confirmed_delete_and_repeated_delete_contracts(client, native_database, accounts, owned_api):
    first = accounts[0]
    vehicle, record = owned_api
    install(client, first)
    before = snapshot(native_database, first.session, vehicle, record)
    fetched = call(client, "GET", vehicle, record)
    assert_headers(fetched, 200, native_database, first)
    assert fetched.json() == record.model_dump(mode="json")
    patched = call(client, "PATCH", vehicle, record, {"service_type": "repair", "description": "Corrected service", "notes": None})
    assert_headers(patched, 200, native_database, first)
    assert patched.json() == {**fetched.json(), "service_type": "repair", "description": "Corrected service", "notes": None}
    assert call(client, "GET", vehicle, record).json() == patched.json()
    removed = call(client, "DELETE", vehicle, record)
    assert_headers(removed, 200, native_database, first)
    assert removed.json() == {"id": record.id, "vehicle_id": vehicle.id, "deleted": True}
    for method in ("DELETE", "GET"):
        missing = call(client, method, vehicle, record)
        assert_headers(missing, 404)
        assert missing.json() == {"detail": "Service record not found."}
    after = snapshot(native_database, first.session, vehicle, record)
    assert after[0] is None and after[1:] == before[1:]
    listed = client.get(f"/api/vehicles/{vehicle.id}/services")
    assert_headers(listed, 200, native_database, first)
    assert listed.json() == {"vehicle_id": vehicle.id, "services": []}


@pytest.mark.parametrize("mileage,hours,cost", list(product([None, "0.0"], [None, "0.0"], [None, "0.00"])))
def test_native_patch_optional_clears_and_zero_preserve_vehicle_readings(client, native_database, accounts, owned_api, mileage, hours, cost):
    first = accounts[0]
    vehicle, record = owned_api
    install(client, first)
    before = snapshot(native_database, first.session, vehicle, record)
    response = call(client, "PATCH", vehicle, record, {"mileage": mileage, "operating_hours": hours, "cost": cost, "notes": " "})
    assert_headers(response, 200, native_database, first)
    assert set(response.json()) == set(service_queries.PUBLIC_FIELDS)
    assert (response.json()["mileage"], response.json()["operating_hours"], response.json()["cost"]) == (mileage, hours, cost)
    assert response.json()["notes"] is None
    assert snapshot(native_database, first.session, vehicle, record)[1:] == before[1:]


@pytest.mark.parametrize("links", [(), ("part",), ("completion",), ("part", "completion")])
def test_native_noop_patch_succeeds_with_any_links(client, native_database, accounts, owned_api, links):
    first = accounts[0]
    vehicle, record = owned_api
    for kind in links:
        add_link(native_database, first.session, vehicle, record, kind)
    install(client, first)
    before = snapshot(native_database, first.session, vehicle, record)
    response = call(client, "PATCH", vehicle, record, {"cost": "42.5", "description": record.description})
    assert_headers(response, 200, native_database, first)
    assert response.json() == record.model_dump(mode="json")
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("fields", [{"notes": "Must not apply"}, {"mileage": None, "cost": None},
                                    {"description": "No partial save", "service_date": "2019-01-01", "operating_hours": "0"}])
def test_native_completion_blocks_patch_with_exact_409_and_no_changes(client, native_database, accounts, owned_api, fields):
    first = accounts[0]
    vehicle, record = owned_api
    add_link(native_database, first.session, vehicle, record, "completion")
    add_link(native_database, first.session, vehicle, record, "part")
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    response = call(client, "PATCH", vehicle, record, fields)
    assert_headers(response, 409)
    assert response.json() == {"detail": "Service record is linked to maintenance completion and cannot be changed."}
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("links", [("part",), ("completion",), ("part", "completion")])
def test_native_linked_removal_has_fixed_409_and_preserves_all_records(client, native_database, accounts, owned_api, links):
    first = accounts[0]
    vehicle, record = owned_api
    for kind in links:
        add_link(native_database, first.session, vehicle, record, kind)
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    response = call(client, "DELETE", vehicle, record)
    assert_headers(response, 409)
    assert response.json() == {"detail": "Service record has linked data and cannot be removed."}
    assert snapshot(native_database, first.session, vehicle, record) == before


def test_native_part_only_edit_is_allowed_and_snapshot_is_unchanged(client, native_database, accounts, owned_api):
    first = accounts[0]
    vehicle, record = owned_api
    add_link(native_database, first.session, vehicle, record, "part")
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    response = call(client, "PATCH", vehicle, record)
    assert_headers(response, 200, native_database, first)
    assert response.json()["notes"] == "Corrected notes"
    assert snapshot(native_database, first.session, vehicle, record)[1:] == before[1:]


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
def test_native_missing_foreign_and_wrong_parent_have_identical_404(client, native_database, accounts, owned_api, method):
    first, second = accounts
    vehicle, record = owned_api
    other = parent(native_database, first)
    body = payload(native_database, first, other)
    gone = service_queries.create_service(native_database.settings, actor=first.session, vehicle_id=other.id, service=ServiceCreate(**body))
    native_database.track_service(gone.id, other.id, first.session.user.id, ServiceCreate(**body))
    service_queries.remove_service(native_database.settings, actor=first.session, vehicle_id=other.id, service_id=gone.id,
                                   confirmation=ServiceRemovalRequest(confirm_removal=True))
    before = snapshot(native_database, first.session, vehicle, record)
    outcomes = []
    for issued, target_vehicle, target_record in ((second, vehicle, record), (first, other, record), (first, other, gone)):
        install(client, issued)
        response = call(client, method, target_vehicle, target_record)
        assert_headers(response, 404)
        outcomes.append(response.json())
    assert outcomes == [{"detail": "Service record not found."}] * 3
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.parametrize("field", ["vehicle_id", "service_id"])
def test_native_noncanonical_path_ids_return_safe_422_without_changes(client, native_database, accounts, owned_api, method, field):
    first = accounts[0]
    vehicle, record = owned_api
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    vehicle_id, service_id = ("0" + str(vehicle.id), str(record.id)) if field == "vehicle_id" else (str(vehicle.id), "0" + str(record.id))
    options = {} if method == "GET" else {"json": {"notes": "No write"} if method == "PATCH" else {"confirm_removal": True}, "headers": AUTH_HEADERS}
    response = client.request(method, f"/api/vehicles/{vehicle_id}/services/{service_id}", **options)
    assert_headers(response, 422)
    assert response.json()["detail"][0]["loc"] == ["path", field]
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("body", [{}, {"confirm_removal": False}, {"confirm_removal": 1}, {"confirm_removal": True, "force": True}])
def test_native_delete_requires_exact_explicit_confirmation(client, native_database, accounts, owned_api, body, caplog):
    first = accounts[0]
    vehicle, record = owned_api
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    response = call(client, "DELETE", vehicle, record, body)
    assert_headers(response, 422)
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("body", [{}, {"description": None}, {"vehicle_id": PRIVATE}, {"notes": PRIVATE + "\x00"},
                                  {"reading_confirmation": {"mileage": PRIVATE}}, {"cost": 0.01}])
def test_native_invalid_patch_is_redacted_without_writes(client, native_database, accounts, owned_api, body, caplog):
    first = accounts[0]
    vehicle, record = owned_api
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    response = call(client, "PATCH", vehicle, record, body)
    assert_headers(response, 422)
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
def test_native_malformed_bodies_are_sanitized(client, native_database, accounts, owned_api, method, caplog):
    first = accounts[0]
    vehicle, record = owned_api
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    response = client.request(method, path(vehicle, record), content="{" + PRIVATE, headers=AUTH_HEADERS)
    assert_headers(response, 422)
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
@pytest.mark.parametrize("case", CSRF_CASES)
def test_native_policy_rejection_precedes_parsing_session_extension_and_business_writes(client, native_database, accounts, owned_api, method, case):
    first = accounts[0]
    vehicle, record = owned_api
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    deadline = stored_deadline(native_database, first)
    response = client.request(method, path(vehicle, record), content="{" + PRIVATE, headers=csrf_headers(case))
    assert_headers(response, 403)
    assert response.json() == {"detail": "Request not allowed."}
    assert stored_deadline(native_database, first) == deadline
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.parametrize("state", ["missing", "revoked"])
def test_native_authentication_failure_clears_cookie_and_preserves_service(client, native_database, accounts, owned_api, method, state):
    first = accounts[0]
    vehicle, record = owned_api
    before = snapshot(native_database, first.session, vehicle, record)
    if state == "revoked":
        install(client, first)
        session_queries.revoke_session(native_database.settings, first.token)
    response = call(client, method, vehicle, record)
    assert_headers(response, 401)
    assert response.json() == {"detail": "Not authenticated."}
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert snapshot(native_database, first.session, vehicle, record) == before


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.parametrize("failure_at", ["preparation", "pre-commit", "lost-ack", "authentication"])
def test_native_failures_discard_prepared_success_preserve_cookie_and_never_retry(client, native_database, accounts, owned_api, method, failure_at, monkeypatch, caplog):
    first = accounts[0]
    vehicle, record = owned_api
    install(client, first)
    before = snapshot(native_database, first.session, vehicle, record)
    original = getattr(service_queries, NAMES[method])
    opened = []
    @contextmanager
    def faulty(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection
            if failure_at == "pre-commit":
                raise psycopg.OperationalError(PRIVATE)
        if failure_at == "lost-ack":
            raise psycopg.OperationalError(PRIVATE)
    def query(settings, **options):
        with monkeypatch.context() as patches:
            patches.setattr(database, "connect_database", faulty)
            return original(settings, **options)
    with monkeypatch.context() as patches:
        patches.setattr(service_queries, NAMES[method], query)
        if failure_at == "preparation":
            def fail_preparation(*args):
                raise RuntimeError(PRIVATE)
            patches.setattr(services, "_service_response", fail_preparation)
        if failure_at == "authentication":
            def fail_authentication(*args):
                raise psycopg.OperationalError(PRIVATE)
            patches.setattr(session_queries, "validate_and_extend_session", fail_authentication)
        response = call(client, method, vehicle, record)
    status = 500 if failure_at == "preparation" else 503
    assert_headers(response, status)
    detail = "Internal server error" if status == 500 else (
        "Authentication unavailable. Please try again." if failure_at == "authentication" else "Service history unavailable. Please try again.")
    assert response.json() == {"detail": detail}
    assert "set-cookie" not in response.headers and client.cookies.get("garageguide_session") is not None
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert len(opened) == (0 if failure_at == "authentication" else 1)
    assert all(connection.closed for connection in opened)
    after = snapshot(native_database, first.session, vehicle, record)
    if failure_at != "lost-ack" or method == "GET":
        assert after == before
    elif method == "PATCH":
        assert service_queries.get_service(native_database.settings, actor=first.session, vehicle_id=vehicle.id, service_id=record.id).notes == "Corrected notes"
        assert after[1:] == before[1:]
    else:
        assert after[0] is None and after[1:] == before[1:]


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
def test_native_success_response_is_prepared_before_commit_and_returned_after_close(client, native_database, accounts, owned_api, method, monkeypatch):
    first = accounts[0]
    vehicle, record = owned_api
    before = snapshot(native_database, first.session, vehicle, record)
    install(client, first)
    original, original_response = getattr(service_queries, NAMES[method]), services._service_response
    opened, prepared = [], []
    @contextmanager
    def observe(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection
    def query(settings, **options):
        with monkeypatch.context() as patches:
            patches.setattr(database, "connect_database", observe)
            return original(settings, **options)
    def prepare(result, actor, status):
        assert opened and not opened[0].closed
        # Read directly through the guarded fixture so observation does not count
        # the verification connection as another business transaction.
        with native_database.connect(native_database.settings, read_only=True) as connection:
            existing = connection.execute(
                "SELECT s.notes FROM public.service_records AS s JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
                (record.id, vehicle.id, first.session.user.id),
            ).fetchone()
        assert existing == (record.notes,)
        prepared.append(result.model_dump(mode="json"))
        return original_response(result, actor, status)
    monkeypatch.setattr(service_queries, NAMES[method], query)
    monkeypatch.setattr(services, "_service_response", prepare)
    response = call(client, method, vehicle, record)
    assert_headers(response, 200, native_database, first)
    assert prepared == [response.json()] and len(opened) == 1 and opened[0].closed
    assert snapshot(native_database, first.session, vehicle, record)[1:] == before[1:]
