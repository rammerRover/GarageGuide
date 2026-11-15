import json
from contextlib import contextmanager
from unittest.mock import Mock

import psycopg
import pytest

from app import database, security, session_queries, vehicle_queries
from app.routes import vehicles
from app.vehicle_schemas import VEHICLE_ID_ERROR, VehicleCreate
from authentication_support import AUTH_HEADERS, CSRF_CASES, csrf_headers
from test_vehicles_integration import (
    DEADLINE, PRIVATE, accounts, assert_private_headers, install, payload, stored_deadline,
)


pytestmark = pytest.mark.integration


@pytest.fixture
def profile(client, native_database, accounts):
    first = accounts[0]
    install(client, first)
    body = payload(native_database, first, engine="V8", mileage="1000.0", operating_hours="10.0")
    response = client.post("/api/vehicles", json=body, headers=AUTH_HEADERS)
    assert_private_headers(response, 201, native_database, first)
    public = response.json()
    native_database.track_vehicle(public["id"], first.session.user.id, VehicleCreate(**body))
    native_database.require_reserved_vehicle(public["id"], first.session.user.id)
    return first, public, "/api/vehicles/" + str(public["id"])


def stored_vehicle(native, issued, vehicle_id):
    return vehicle_queries.get_vehicle(native.settings, actor=issued.session, vehicle_id=vehicle_id).model_dump(mode="json")


@pytest.mark.parametrize("mileage,hours", [(None, None), ("0.0", None), (None, "0.0"), ("99999999999.9", "12.3")])
def test_public_detail_and_patch_reading_combinations_commit_with_exact_deadline(client, native_database, profile, mileage, hours):
    issued, original, path = profile
    loaded = client.get(path)
    assert_private_headers(loaded, 200, native_database, issued)
    assert loaded.json() == original and "set-cookie" not in loaded.headers
    saved = client.patch(path, json={"mileage": mileage, "operating_hours": hours,
        "reading_confirmation": {"mileage": "1000.0", "operating_hours": "10.0"}}, headers=AUTH_HEADERS)
    assert_private_headers(saved, 200, native_database, issued)
    public = saved.json()
    assert set(public) == set(vehicle_queries.PUBLIC_FIELDS)
    assert public["mileage"] == mileage and public["operating_hours"] == hours
    assert public["created_at"] == original["created_at"] and public["readings_updated_at"] is not None
    assert "set-cookie" not in saved.headers
    assert stored_vehicle(native_database, issued, original["id"]) == public


@pytest.mark.parametrize("fields", [{"model": "Updated model"}, {"engine": None}, {"engine": "  "}, {"mileage": "01000.0", "operating_hours": "10"}])
def test_partial_text_null_and_noop_updates_preserve_reading_timestamp(client, native_database, profile, fields):
    issued, original, path = profile
    saved = client.patch(path, json=fields, headers={**AUTH_HEADERS, "Content-Type": "application/json; charset=utf-8"})
    assert_private_headers(saved, 200, native_database, issued)
    result = saved.json()
    assert result["readings_updated_at"] == original["readings_updated_at"]
    assert result["created_at"] == original["created_at"] and result["id"] == original["id"]
    assert result["make"] == original["make"] and result["year"] == original["year"]
    if "engine" in fields:
        assert result["engine"] is None
    assert stored_vehicle(native_database, issued, original["id"]) == result


def test_legacy_year_is_readable_and_omittable_but_not_valid_supplied_year(client, native_database, profile):
    issued, original, path = profile
    with native_database.connect(native_database.settings) as connection:
        connection.execute("UPDATE public.vehicles SET year = %s WHERE id = %s AND user_id = %s", (1, original["id"], issued.session.user.id))
    assert client.get(path).json()["year"] == 1
    saved = client.patch(path, json={"model": "Legacy model edit"}, headers=AUTH_HEADERS)
    assert_private_headers(saved, 200, native_database, issued)
    assert saved.json()["year"] == 1 and saved.json()["readings_updated_at"] == original["readings_updated_at"]
    rejected = client.patch(path, json={"year": 1}, headers=AUTH_HEADERS)
    assert_private_headers(rejected, 422)
    assert stored_vehicle(native_database, issued, original["id"]) == saved.json()


@pytest.mark.parametrize("method", ["GET", "PATCH"])
def test_missing_and_foreign_profile_are_indistinguishable_and_do_not_modify_owner(client, native_database, accounts, profile, method):
    first, original, foreign_path = profile
    second = accounts[1]
    install(client, second)
    body = payload(native_database, second)
    created = client.post("/api/vehicles", json=body, headers=AUTH_HEADERS)
    assert_private_headers(created, 201, native_database, second)
    missing_id = created.json()["id"]
    native_database.track_vehicle(missing_id, second.session.user.id, VehicleCreate(**body))
    with native_database.connect(native_database.settings) as connection:
        connection.execute("DELETE FROM public.vehicles WHERE id = %s AND user_id = %s", (missing_id, second.session.user.id))
    responses = []
    for path in [foreign_path, "/api/vehicles/" + str(missing_id)]:
        response = client.request(method, path, **({"json": {"model": "Must not apply"}, "headers": AUTH_HEADERS} if method == "PATCH" else {}))
        assert_private_headers(response, 404)
        assert response.json() == {"detail": "Vehicle not found."} and "set-cookie" not in response.headers
        responses.append(response)
    assert responses[0].content == responses[1].content and dict(responses[0].headers) == dict(responses[1].headers)
    assert stored_vehicle(native_database, first, original["id"]) == original


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("new", [None, "0.0"])
def test_full_lower_or_clear_confirmation_exchange(client, native_database, profile, field, new):
    issued, original, path = profile
    denied = client.patch(path, json={field: new}, headers=AUTH_HEADERS)
    assert_private_headers(denied, 409)
    assert denied.json() == {"detail": "Reading changes require confirmation.", "fields": [field], "current_readings": {field: original[field]}}
    assert stored_vehicle(native_database, issued, original["id"]) == original
    saved = client.patch(path, json={field: new, "reading_confirmation": denied.json()["current_readings"]}, headers=AUTH_HEADERS)
    assert_private_headers(saved, 200, native_database, issued)
    assert saved.json()[field] == new
    assert stored_vehicle(native_database, issued, original["id"]) == saved.json()


def test_two_reading_rejection_is_atomic_until_both_confirmed(client, native_database, profile):
    issued, original, path = profile
    changes = {"model": "Confirmed edit", "mileage": None, "operating_hours": "9.0"}
    denied = client.patch(path, json={**changes, "reading_confirmation": {"mileage": "1000"}}, headers=AUTH_HEADERS)
    assert_private_headers(denied, 409)
    assert denied.json()["fields"] == ["mileage", "operating_hours"]
    assert stored_vehicle(native_database, issued, original["id"]) == original
    saved = client.patch(path, json={**changes, "reading_confirmation": denied.json()["current_readings"]}, headers=AUTH_HEADERS)
    assert_private_headers(saved, 200, native_database, issued)
    assert all(saved.json()[field] == value for field, value in changes.items())


@pytest.mark.parametrize("replacement,required", [("1200.0", True), ("800.0", False), ("900.0", False), (None, False)])
def test_stale_confirmation_returns_current_fields_only_and_writes_nothing(client, native_database, profile, replacement, required):
    issued, original, path = profile
    first = client.patch(path, json={"mileage": "900.0"}, headers=AUTH_HEADERS)
    assert_private_headers(first, 409)
    intervening = client.patch(path, json={"mileage": replacement, "reading_confirmation": {"mileage": "1000"}}, headers=AUTH_HEADERS)
    assert_private_headers(intervening, 200, native_database, issued)
    stale = client.patch(path, json={"model": "Must not apply", "mileage": "900.0", "reading_confirmation": first.json()["current_readings"]}, headers=AUTH_HEADERS)
    assert_private_headers(stale, 409)
    assert stale.json() == {"detail": "Reading changes require confirmation.",
        "fields": ["mileage"] if required else [], "current_readings": {"mileage": replacement} if required else {}}
    assert stored_vehicle(native_database, issued, original["id"]) == intervening.json()


def test_stale_now_increasing_reading_is_omitted_from_other_required_field_response(client, native_database, profile):
    issued, original, path = profile
    prior = client.patch(path, json={"mileage": "800", "reading_confirmation": {"mileage": "1000"}}, headers=AUTH_HEADERS)
    assert_private_headers(prior, 200, native_database, issued)
    denied = client.patch(path, json={"mileage": "900", "operating_hours": None,
        "reading_confirmation": {"mileage": "1000", "operating_hours": "10"}}, headers=AUTH_HEADERS)
    assert_private_headers(denied, 409)
    assert denied.json() == {"detail": "Reading changes require confirmation.", "fields": ["operating_hours"], "current_readings": {"operating_hours": "10.0"}}
    assert stored_vehicle(native_database, issued, original["id"]) == prior.json()


@pytest.mark.parametrize("case", CSRF_CASES)
def test_native_patch_policy_rejection_does_not_parse_or_touch_session_or_vehicle(client, native_database, profile, case):
    issued, original, path = profile
    before = stored_deadline(native_database, issued)
    response = client.patch(path, content="{" + PRIVATE, headers=csrf_headers(case))
    assert_private_headers(response, 403)
    assert response.json() == {"detail": "Request not allowed."} and PRIVATE not in response.text
    assert stored_deadline(native_database, issued) == before
    assert stored_vehicle(native_database, issued, original["id"]) == original


@pytest.mark.parametrize("method", ["GET", "PATCH"])
def test_native_canonical_id_rejections_never_reach_business_queries(client, native_database, profile, monkeypatch, method):
    issued, original, _ = profile
    name = "get_vehicle" if method == "GET" else "update_vehicle"
    spy = Mock(wraps=getattr(vehicle_queries, name))
    with monkeypatch.context() as patches:
        patches.setattr(vehicle_queries, name, spy)
        for path in ["0", "01", "%30%31", "+1", "1.0", "%201", "%D9%A1", "2147483648", PRIVATE]:
            response = client.request(method, "/api/vehicles/" + path, **({"json": {"model": "Must not apply"}, "headers": AUTH_HEADERS} if method == "PATCH" else {}))
            assert_private_headers(response, 422)
            assert response.json() == {"detail": [{"loc": ["path", "vehicle_id"], "msg": VEHICLE_ID_ERROR, "type": "value_error"}]}
        spy.assert_not_called()
    assert stored_vehicle(native_database, issued, original["id"]) == original


@pytest.mark.parametrize("body", [{}, {"reading_confirmation": {}}, {"make": None}, {"owner_id": PRIVATE}, {"mileage": PRIVATE},
    {"mileage": None, "reading_confirmation": {PRIVATE: PRIVATE}}, {"mileage": None, "reading_confirmation": {"mileage": PRIVATE}}, {"engine": PRIVATE + "\ud800"}])
def test_native_invalid_patch_is_redacted_without_partial_changes(client, native_database, profile, caplog, body):
    issued, original, path = profile
    response = client.patch(path, content=json.dumps(body), headers=AUTH_HEADERS)
    assert_private_headers(response, 422)
    assert PRIVATE not in response.text + caplog.text
    assert all(set(item) == {"loc", "msg", "type"} for item in response.json()["detail"])
    assert stored_vehicle(native_database, issued, original["id"]) == original


def test_native_malformed_patch_is_redacted_without_partial_changes(client, native_database, profile, caplog):
    issued, original, path = profile
    response = client.patch(path, content='{"model":"' + PRIVATE, headers=AUTH_HEADERS)
    assert_private_headers(response, 422)
    assert PRIVATE not in response.text + caplog.text
    assert stored_vehicle(native_database, issued, original["id"]) == original


@pytest.mark.parametrize("method", ["GET", "PATCH"])
@pytest.mark.parametrize("state", ["missing", "malformed", "unknown", "expired", "revoked"])
def test_native_detail_requires_valid_session_and_clears_only_unusable_cookie(client, native_database, profile, method, state):
    issued, original, path = profile
    client.cookies.clear()
    if state in ("expired", "revoked"):
        install(client, issued)
        if state == "revoked":
            session_queries.revoke_session(native_database.settings, issued.token)
        else:
            with native_database.connect(native_database.settings) as connection:
                connection.execute("UPDATE public.user_sessions SET created_at = clock_timestamp() - INTERVAL '1 hour', expires_at = clock_timestamp() - INTERVAL '1 minute' WHERE id = %s AND user_id = %s", (issued.session.session_id, issued.session.user.id))
    elif state != "missing":
        client.cookies.set("garageguide_session", "synthetic-malformed" if state == "malformed" else security.generate_session_token().get_secret_value())
    response = client.request(method, path, **({"json": {"model": "Must not apply"}, "headers": AUTH_HEADERS} if method == "PATCH" else {}))
    assert_private_headers(response, 401)
    assert response.json() == {"detail": "Not authenticated."}
    cookie = response.headers["set-cookie"].lower()
    assert all(value in cookie for value in ["max-age=0", "httponly", "samesite=lax", "path=/"])
    assert stored_vehicle(native_database, issued, original["id"]) == original


@pytest.mark.parametrize("phase", ["prepare", "business", "commit", "lost-ack", "authentication", "unexpected"])
def test_native_api_failures_preserve_cookie_and_prove_commit_or_rollback_with_cleanup(client, native_database, profile, monkeypatch, caplog, phase):
    issued, original, path = profile
    real_update = vehicle_queries.update_vehicle
    opened = []

    @contextmanager
    def faulty_connection(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection
            if phase == "commit":
                raise psycopg.OperationalError(PRIVATE)
        if phase == "lost-ack":
            raise psycopg.OperationalError(PRIVATE)

    def update_with_fault(settings, **options):
        with monkeypatch.context() as patches:
            patches.setattr(database, "connect_database", faulty_connection)
            return real_update(settings, **options)

    with monkeypatch.context() as patches:
        if phase == "prepare":
            patches.setattr(vehicles, "_vehicle_response", Mock(side_effect=RuntimeError(PRIVATE)))
        elif phase in ["commit", "lost-ack"]:
            patches.setattr(vehicle_queries, "update_vehicle", update_with_fault)
        elif phase == "authentication":
            patches.setattr(session_queries, "validate_and_extend_session", Mock(side_effect=psycopg.OperationalError(PRIVATE)))
        else:
            failure = vehicle_queries.VehicleUnavailableError() if phase == "business" else RuntimeError(PRIVATE)
            patches.setattr(vehicle_queries, "update_vehicle", Mock(side_effect=failure))
        response = client.patch(path, json={"model": "Possible committed update"}, headers=AUTH_HEADERS)
    status = 500 if phase in ["prepare", "unexpected"] else 503
    assert_private_headers(response, status)
    detail = "Internal server error" if status == 500 else "Authentication unavailable. Please try again." if phase == "authentication" else "Vehicles unavailable. Please try again."
    assert response.json() == {"detail": detail}
    assert "set-cookie" not in response.headers and client.cookies.get("garageguide_session") is not None
    assert PRIVATE not in response.text + caplog.text
    assert all(not record.exc_info and not record.args for record in caplog.records if record.name.startswith("app."))
    if phase in ["commit", "lost-ack"]:
        assert len(opened) == 1 and opened[0].closed
    stored = stored_vehicle(native_database, issued, original["id"])
    assert stored["model"] == ("Possible committed update" if phase == "lost-ack" else original["model"])
    native_database.cleanup()
    assert native_database.cleanup_verified and native_database.cleanup_vehicle_count == 1
    assert native_database.cleanup_counts == (2, 2)


def test_native_response_preparation_sees_uncommitted_values_and_only_one_authentication(client, native_database, profile, monkeypatch):
    issued, original, path = profile
    original_response = vehicles._vehicle_response
    session_spy = Mock(wraps=session_queries.validate_and_extend_session)
    prepared = []

    def prepare(result, actor, status):
        assert result.model == "Prepared before commit"
        assert stored_vehicle(native_database, issued, original["id"]) == original
        prepared.append(True)
        return original_response(result, actor, status)

    with monkeypatch.context() as patches:
        patches.setattr(vehicles, "_vehicle_response", prepare)
        patches.setattr(session_queries, "validate_and_extend_session", session_spy)
        response = client.patch(path, json={"model": "Prepared before commit"}, headers=AUTH_HEADERS)
    assert_private_headers(response, 200, native_database, issued)
    session_spy.assert_called_once()
    assert prepared == [True] and stored_vehicle(native_database, issued, original["id"]) == response.json()
