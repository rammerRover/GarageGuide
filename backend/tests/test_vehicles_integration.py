import json
from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4

import psycopg
import pytest

from app import authentication, database, security, session_queries, user_queries, vehicle_queries
from app.routes import vehicles
from app.schemas import RegistrationResponse
from app.vehicle_schemas import VehicleCreate
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers


pytestmark = pytest.mark.integration
DEADLINE = authentication.SESSION_DEADLINE_HEADER
PRIVATE = "synthetic-private-vehicle-marker"


@pytest.fixture
def accounts(native_database):
    result = []
    for _ in range(2):
        email = native_database.reserve_email()
        row = user_queries.create_user(
            native_database.settings, email=email, password_hash="synthetic-unused-credential",
        )
        user = RegistrationResponse(id=row[0], email=row[1], created_at=row[2])
        native_database.track_user(user.id, user.email)
        issued = session_queries.create_session(native_database.settings, user=user)
        native_database.track_session(issued.session.session_id, user.id)
        result.append(issued)
    return result


def install(client, issued):
    client.cookies.clear()
    client.cookies.set("garageguide_session", issued.token.get_secret_value())


def payload(native, issued, **changes):
    body = {
        "year": 2020, "make": "Synthetic' -- \u00e9", "model": f"gg-api-{uuid4().hex}",
        "vehicle_type": "Custom \U0001f6f5", **changes,
    }
    native.reserve_vehicle(issued.session.user.id, VehicleCreate(**body))
    return body


def owned_rows(native, issued):
    with native.connect(native.settings, read_only=True) as connection:
        return connection.execute(
            "SELECT id FROM public.vehicles WHERE user_id = %s ORDER BY id", (issued.session.user.id,),
        ).fetchall()


def stored_deadline(native, issued):
    with native.connect(native.settings, read_only=True) as connection:
        return connection.execute(
            "SELECT expires_at FROM public.user_sessions WHERE id = %s AND user_id = %s",
            (issued.session.session_id, issued.session.user.id),
        ).fetchone()[0]


def assert_private_headers(response, status, native=None, issued=None):
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"
    if status in (200, 201):
        assert datetime.fromisoformat(response.headers[DEADLINE]) == stored_deadline(native, issued)
    else:
        assert DEADLINE not in response.headers


@pytest.mark.parametrize(
    ("mileage", "hours"), [(None, None), ("0.0", None), (None, "0.0"), ("99999999999.9", "12.3")],
)
def test_native_creation_is_committed_public_and_owned(client, native_database, accounts, mileage, hours):
    first, second = accounts
    install(client, first)
    empty = client.get("/api/vehicles")
    assert_private_headers(empty, 200, native_database, first)
    assert empty.json() == {"vehicles": []}
    body = payload(native_database, first, mileage=mileage, operating_hours=hours)
    created = client.post("/api/vehicles?user_id=" + str(second.session.user.id), json=body,
                          headers={**AUTH_HEADERS, "Content-Type": "application/json; charset=utf-8"})
    assert_private_headers(created, 201, native_database, first)
    public = created.json()
    assert set(public) == {"id", "year", "make", "model", "engine", "vehicle_type", "mileage",
                           "operating_hours", "readings_updated_at", "created_at"}
    assert public["mileage"] == mileage and public["operating_hours"] == hours
    assert (public["readings_updated_at"] is None) == (mileage is None and hours is None)
    native_database.track_vehicle(public["id"], first.session.user.id, VehicleCreate(**body))
    assert owned_rows(native_database, first) == [(public["id"],)]
    listed = client.get("/api/vehicles?user_id=" + str(second.session.user.id))
    assert_private_headers(listed, 200, native_database, first)
    assert listed.json() == {"vehicles": [public]}
    install(client, second)
    assert client.get("/api/vehicles").json() == {"vehicles": []}
    other_body = payload(native_database, second)
    other = client.post("/api/vehicles", json=other_body, headers=AUTH_HEADERS)
    assert_private_headers(other, 201, native_database, second)
    assert client.get("/api/vehicles").json() == {"vehicles": [other.json()]}
    install(client, first)
    assert client.get("/api/vehicles").json() == {"vehicles": [public]}


def test_native_identical_posts_remain_distinct(client, native_database, accounts):
    first = accounts[0]
    install(client, first)
    body = payload(native_database, first)
    ids = []
    for _ in range(2):
        response = client.post("/api/vehicles", json=body, headers=AUTH_HEADERS)
        assert_private_headers(response, 201, native_database, first)
        ids.append(response.json()["id"])
    assert ids[0] != ids[1]
    assert [item["id"] for item in client.get("/api/vehicles").json()["vehicles"]] == ids[::-1]


@pytest.mark.parametrize("case", CSRF_CASES)
def test_native_policy_denial_has_no_vehicle_or_session_writes(client, native_database, accounts, case):
    first = accounts[0]
    install(client, first)
    before = stored_deadline(native_database, first)
    response = client.post("/api/vehicles", content="{" + PRIVATE, headers=csrf_headers(case))
    assert_private_headers(response, 403)
    assert response.json() == {"detail": "Request not allowed."}
    assert PRIVATE not in response.text
    assert owned_rows(native_database, first) == []
    assert stored_deadline(native_database, first) == before


@pytest.mark.parametrize("changes", [{"user_id": 999}, {"owner_id": 999}, {"id": 999},
                                     {"created_at": PRIVATE}, {"make": PRIVATE + "\x00"},
                                     {"engine": PRIVATE + "\ud800"}, {"mileage": PRIVATE},
                                     {"operating_hours": 0}, {"year": 1885}])
def test_native_invalid_data_cannot_write_or_leak(client, native_database, accounts, changes, caplog):
    first = accounts[0]
    install(client, first)
    body = {"year": 2020, "make": "Synthetic", "model": "Test", "vehicle_type": "Test", **changes}
    response = client.post("/api/vehicles", content=json.dumps(body), headers=AUTH_HEADERS)
    assert_private_headers(response, 422)
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert all(set(entry) == {"loc", "msg", "type"} for entry in response.json()["detail"])
    assert owned_rows(native_database, first) == []


def test_native_malformed_json_is_sanitized(client, native_database, accounts, caplog):
    install(client, accounts[0])
    response = client.post("/api/vehicles", content='{"make":"' + PRIVATE, headers=AUTH_HEADERS)
    assert_private_headers(response, 422)
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert owned_rows(native_database, accounts[0]) == []


@pytest.mark.parametrize("state", ["missing", "malformed", "unknown", "expired", "revoked"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_native_unusable_session_rejected_without_vehicle_write(client, native_database, accounts, state, method):
    first = accounts[0]
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
        client.cookies.set("garageguide_session", "malformed" if state == "malformed" else security.generate_session_token().get_secret_value())
    response = client.request(method, "/api/vehicles", **({"json": {"year": 2020, "make": "Test", "model": "Test", "vehicle_type": "Test"}, "headers": AUTH_HEADERS} if method == "POST" else {}))
    assert_private_headers(response, 401)
    assert response.json() == {"detail": "Not authenticated."}
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert owned_rows(native_database, first) == []


@pytest.mark.parametrize("failure_at", ["preparation", "business", "commit", "lost-ack", "authentication"])
def test_native_failures_preserve_cookie_and_exact_cleanup(client, native_database, accounts, monkeypatch, caplog, failure_at):
    first = accounts[0]
    install(client, first)
    body = payload(native_database, first)
    original = vehicle_queries.create_vehicle

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
            return original(settings, **kwargs)

    with monkeypatch.context() as patches:
        if failure_at == "preparation":
            def fail_preparation(*args):
                raise RuntimeError(PRIVATE)
            patches.setattr(vehicles, "_vehicle_response", fail_preparation)
        elif failure_at in ("commit", "lost-ack"):
            patches.setattr(vehicle_queries, "create_vehicle", failed_creation)
        elif failure_at == "authentication":
            def fail_authentication(*args):
                raise psycopg.OperationalError(PRIVATE)
            patches.setattr(session_queries, "validate_and_extend_session", fail_authentication)
        else:
            def fail_business(*args, **kwargs):
                raise vehicle_queries.VehicleUnavailableError()
            patches.setattr(vehicle_queries, "create_vehicle", fail_business)
        response = client.post("/api/vehicles", json=body, headers=AUTH_HEADERS)
    status = 500 if failure_at == "preparation" else 503
    assert_private_headers(response, status)
    detail = "Internal server error" if status == 500 else "Authentication unavailable. Please try again." if failure_at == "authentication" else "Vehicles unavailable. Please try again."
    assert response.json() == {"detail": detail}
    assert "set-cookie" not in response.headers
    assert client.cookies.get("garageguide_session") is not None
    assert PRIVATE not in response.text and PRIVATE not in caplog.text
    assert len(owned_rows(native_database, first)) == (1 if failure_at == "lost-ack" else 0)
    native_database.cleanup()
    assert native_database.cleanup_verified
    assert native_database.cleanup_vehicle_count == (1 if failure_at == "lost-ack" else 0)
    assert native_database.cleanup_counts == (2, 2)
