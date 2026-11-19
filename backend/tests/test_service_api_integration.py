import json
from contextlib import contextmanager
from datetime import datetime
from itertools import product
from uuid import uuid4

import psycopg
import pytest

from app import authentication, database, security, service_queries, session_queries, vehicle_queries
from app.routes import services
from app.service_schemas import ServiceCreate
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers
from test_vehicle_queries_integration import create_owned, reserved_vehicle
from test_vehicles_integration import accounts, install, stored_deadline


pytestmark = pytest.mark.integration
DEADLINE = authentication.SESSION_DEADLINE_HEADER
PRIVATE = "synthetic-private-service-marker"


def parent(native, issued):
    actor = issued.session
    return create_owned(native, actor, reserved_vehicle(native, actor, mileage="1000.0", operating_hours="10.0"))


def path(vehicle):
    return f"/api/vehicles/{vehicle.id}/services"


def payload(native, issued, vehicle, **changes):
    body = {"service_date": "2020-02-29", "service_type": "maintenance",
            "description": f"gg-service-api-{uuid4().hex} Quote' -- \u00e9", **changes}
    native.reserve_service(vehicle.id, issued.session.user.id, ServiceCreate(**body))
    return body


def owned_rows(native, issued, vehicle):
    with native.connect(native.settings, read_only=True) as connection:
        return connection.execute(
            "SELECT s.id FROM public.service_records AS s JOIN public.vehicles AS v ON v.id = s.vehicle_id "
            "WHERE s.vehicle_id = %s AND v.user_id = %s ORDER BY s.id",
            (vehicle.id, issued.session.user.id),
        ).fetchall()


def assert_headers(response, status, native=None, issued=None):
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"
    if status in (200, 201):
        assert datetime.fromisoformat(response.headers[DEADLINE]) == stored_deadline(native, issued)
    else:
        assert DEADLINE not in response.headers


@pytest.mark.parametrize("mileage,hours,cost", list(product([None, "0.0"], [None, "0.0"], [None, "0.00"])))
def test_native_empty_list_and_committed_public_creation_leave_vehicle_unchanged(client, native_database, accounts, mileage, hours, cost):
    first, second = accounts
    vehicle = parent(native_database, first)
    before = vehicle_queries.get_vehicle(native_database.settings, actor=first.session, vehicle_id=vehicle.id)
    install(client, first)
    empty = client.get(path(vehicle))
    assert_headers(empty, 200, native_database, first)
    assert empty.json() == {"vehicle_id": vehicle.id, "services": []}
    body = payload(native_database, first, vehicle, mileage=mileage, operating_hours=hours, cost=cost)
    created = client.post(path(vehicle) + f"?user_id={second.session.user.id}", json=body,
                          headers={**AUTH_HEADERS, "Content-Type": "application/json; charset=utf-8"})
    assert_headers(created, 201, native_database, first)
    public = created.json()
    assert set(public) == set(service_queries.PUBLIC_FIELDS)
    assert public["vehicle_id"] == vehicle.id and public["service_date"] == body["service_date"]
    assert (public["mileage"], public["operating_hours"], public["cost"]) == (mileage, hours, cost)
    assert "set-cookie" not in created.headers
    native_database.track_service(public["id"], vehicle.id, first.session.user.id, ServiceCreate(**body))
    assert owned_rows(native_database, first, vehicle) == [(public["id"],)]
    listed = client.get(path(vehicle))
    assert_headers(listed, 200, native_database, first)
    assert listed.json() == {"vehicle_id": vehicle.id, "services": [public]}
    assert vehicle_queries.get_vehicle(native_database.settings, actor=first.session, vehicle_id=vehicle.id) == before


def test_native_accounts_and_owned_parent_vehicles_are_isolated(client, native_database, accounts):
    first, second = accounts
    vehicles = [parent(native_database, first), parent(native_database, second)]
    publics = []
    for issued, vehicle in zip(accounts, vehicles, strict=True):
        install(client, issued)
        response = client.post(path(vehicle), json=payload(native_database, issued, vehicle), headers=AUTH_HEADERS)
        assert_headers(response, 201, native_database, issued)
        publics.append(response.json())
    for index, issued in enumerate(accounts):
        install(client, issued)
        listed = client.get(path(vehicles[index]))
        assert_headers(listed, 200, native_database, issued)
        assert listed.json()["services"] == [publics[index]]
        foreign = client.get(path(vehicles[1 - index]))
        assert_headers(foreign, 404)
        assert foreign.json() == {"detail": "Vehicle not found."}
    empty_vehicle = parent(native_database, first)
    install(client, first)
    assert client.get(path(empty_vehicle)).json() == {"vehicle_id": empty_vehicle.id, "services": []}


def test_native_identical_posts_are_distinct_and_listed_newest_first(client, native_database, accounts):
    first = accounts[0]
    vehicle = parent(native_database, first)
    install(client, first)
    body = payload(native_database, first, vehicle)
    ids = []
    for _ in range(2):
        response = client.post(path(vehicle), json=body, headers=AUTH_HEADERS)
        assert_headers(response, 201, native_database, first)
        ids.append(response.json()["id"])
    assert ids[0] != ids[1]
    older = client.post(path(vehicle), json=payload(native_database, first, vehicle, service_date="2019-01-01"), headers=AUTH_HEADERS)
    assert_headers(older, 201, native_database, first)
    listed = client.get(path(vehicle))
    assert_headers(listed, 200, native_database, first)
    assert [record["id"] for record in listed.json()["services"]] == [ids[1], ids[0], older.json()["id"]]


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_native_missing_and_foreign_parents_return_identical_404(client, native_database, accounts, method):
    first, second = accounts
    owned, foreign, missing = parent(native_database, first), parent(native_database, second), parent(native_database, first)
    with native_database.connect(native_database.settings) as connection:
        connection.execute("DELETE FROM public.vehicles WHERE id = %s AND user_id = %s", (missing.id, first.session.user.id))
    body = payload(native_database, first, owned)
    install(client, first)
    outcomes = []
    for vehicle in (missing, foreign):
        response = client.request(method, path(vehicle), **({"json": body, "headers": AUTH_HEADERS} if method == "POST" else {}))
        assert_headers(response, 404)
        outcomes.append(response.json())
    assert outcomes == [{"detail": "Vehicle not found."}] * 2
    assert owned_rows(native_database, second, foreign) == []


@pytest.mark.parametrize("case", CSRF_CASES)
def test_native_policy_denial_does_not_parse_or_write_or_extend_session(client, native_database, accounts, case, caplog):
    first = accounts[0]
    vehicle = parent(native_database, first)
    install(client, first)
    before = stored_deadline(native_database, first)
    response = client.post(path(vehicle), content="{" + PRIVATE, headers=csrf_headers(case))
    assert_headers(response, 403)
    assert response.json() == {"detail": "Request not allowed."}
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert owned_rows(native_database, first, vehicle) == []
    assert stored_deadline(native_database, first) == before


@pytest.mark.parametrize("changes", [{"user_id": PRIVATE}, {"vehicle_id": PRIVATE}, {"cost": 0.01},
                                     {"notes": PRIVATE + "\x00"}, {"service_type": PRIVATE}, {"service_date": "2099-01-01"}])
def test_native_invalid_body_is_redacted_and_cannot_create(client, native_database, accounts, changes, caplog):
    first = accounts[0]
    vehicle = parent(native_database, first)
    body = payload(native_database, first, vehicle)
    install(client, first)
    response = client.post(path(vehicle), content=json.dumps({**body, **changes}), headers=AUTH_HEADERS)
    assert_headers(response, 422)
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert owned_rows(native_database, first, vehicle) == []


def test_native_malformed_json_is_safe_and_cannot_create(client, native_database, accounts, caplog):
    first = accounts[0]
    vehicle = parent(native_database, first)
    install(client, first)
    response = client.post(path(vehicle), content='{"description":"' + PRIVATE, headers=AUTH_HEADERS)
    assert_headers(response, 422)
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert owned_rows(native_database, first, vehicle) == []


@pytest.mark.parametrize("state", ["missing", "malformed", "unknown", "expired", "revoked"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_native_unusable_sessions_clear_cookie_without_creating_services(client, native_database, accounts, state, method):
    first = accounts[0]
    vehicle = parent(native_database, first)
    body = payload(native_database, first, vehicle)
    if state in ("expired", "revoked"):
        install(client, first)
        if state == "revoked":
            session_queries.revoke_session(native_database.settings, first.token)
        else:
            with native_database.connect(native_database.settings) as connection:
                connection.execute(
                    "UPDATE public.user_sessions SET created_at = clock_timestamp() - INTERVAL '1 hour', "
                    "expires_at = clock_timestamp() - INTERVAL '1 minute' WHERE id = %s AND user_id = %s",
                    (first.session.session_id, first.session.user.id),
                )
    elif state != "missing":
        client.cookies.set("garageguide_session", PRIVATE if state == "malformed" else security.generate_session_token().get_secret_value())
    response = client.request(method, path(vehicle), **({"json": body, "headers": AUTH_HEADERS} if method == "POST" else {}))
    assert_headers(response, 401)
    assert response.json() == {"detail": "Not authenticated."}
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert owned_rows(native_database, first, vehicle) == []


def test_native_response_is_prepared_inside_transaction_and_201_follows_commit_and_close(client, native_database, accounts, monkeypatch):
    first = accounts[0]
    vehicle = parent(native_database, first)
    body = payload(native_database, first, vehicle)
    install(client, first)
    original_response, original_create = services._service_response, service_queries.create_service
    opened, prepared = [], []

    @contextmanager
    def observe(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection

    def creating(settings, **kwargs):
        with monkeypatch.context() as patches:
            patches.setattr(database, "connect_database", observe)
            return original_create(settings, **kwargs)

    def prepare(record, actor, status):
        assert opened and not opened[0].closed
        assert owned_rows(native_database, first, vehicle) == []
        prepared.append(record.id)
        return original_response(record, actor, status)

    monkeypatch.setattr(service_queries, "create_service", creating)
    monkeypatch.setattr(services, "_service_response", prepare)
    response = client.post(path(vehicle), json=body, headers=AUTH_HEADERS)
    assert_headers(response, 201, native_database, first)
    assert prepared == [response.json()["id"]] and len(opened) == 1 and opened[0].closed
    assert owned_rows(native_database, first, vehicle) == [(response.json()["id"],)]


@pytest.mark.parametrize("method,failure_at", [
    ("POST", "preparation"), ("POST", "business"), ("POST", "commit"), ("POST", "lost-ack"),
    ("POST", "authentication"), ("POST", "unexpected"), ("GET", "authentication"), ("GET", "business"),
])
def test_native_failures_preserve_cookie_redact_details_and_cleanup_exactly(client, native_database, accounts, monkeypatch, method, failure_at, caplog):
    first = accounts[0]
    vehicle = parent(native_database, first)
    body = payload(native_database, first, vehicle)
    install(client, first)
    original_create = service_queries.create_service

    @contextmanager
    def faulty_connection(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            yield connection
            if failure_at == "commit":
                raise psycopg.OperationalError(PRIVATE)
        if failure_at == "lost-ack":
            raise psycopg.OperationalError(PRIVATE)

    def failed_creation(settings, **kwargs):
        with monkeypatch.context() as patches:
            patches.setattr(database, "connect_database", faulty_connection)
            return original_create(settings, **kwargs)

    with monkeypatch.context() as patches:
        if failure_at == "preparation":
            def fail_preparation(*args):
                raise RuntimeError(PRIVATE)
            patches.setattr(services, "_service_response", fail_preparation)
        elif failure_at in ("commit", "lost-ack"):
            patches.setattr(service_queries, "create_service", failed_creation)
        elif failure_at == "authentication":
            def fail_authentication(*args):
                raise psycopg.OperationalError(PRIVATE)
            patches.setattr(session_queries, "validate_and_extend_session", fail_authentication)
        else:
            error = service_queries.ServiceUnavailableError() if failure_at == "business" else RuntimeError(PRIVATE)
            def failed_business(*args, **kwargs):
                raise error
            patches.setattr(service_queries, "create_service" if method == "POST" else "list_services", failed_business)
        response = client.request(method, path(vehicle), **({"json": body, "headers": AUTH_HEADERS} if method == "POST" else {}))
    status = 500 if failure_at in ("preparation", "unexpected") else 503
    assert_headers(response, status)
    detail = "Internal server error" if status == 500 else (
        "Authentication unavailable. Please try again." if failure_at == "authentication" else "Service history unavailable. Please try again.")
    assert response.json() == {"detail": detail}
    assert "set-cookie" not in response.headers and client.cookies.get("garageguide_session") is not None
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert len(owned_rows(native_database, first, vehicle)) == (1 if failure_at == "lost-ack" else 0)
    native_database.cleanup()
    assert native_database.cleanup_verified
    assert native_database.cleanup_service_count == (1 if failure_at == "lost-ack" else 0)
    assert native_database.cleanup_vehicle_count == 1 and native_database.cleanup_counts == (2, 2)


def test_native_logout_rejects_service_access_and_health_stays_public(client, native_database, accounts):
    first = accounts[0]
    vehicle = parent(native_database, first)
    install(client, first)
    assert_headers(client.get(path(vehicle)), 200, native_database, first)
    assert client.post("/api/auth/logout", json={}, headers=AUTH_HEADERS).status_code == 204
    assert_headers(client.get(path(vehicle)), 401)
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/health/db").status_code == 200
