from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import psycopg
import pytest
from starlette.requests import Request

from app import authentication, database, session_queries
from app.maintenance_schedule_schemas import DUPLICATE_NAME_DETAIL, EMPTY_PATCH_ERROR
from app.schemas import RegistrationResponse
from authentication_support import AUTH_HEADERS, csrf_headers
from test_maintenance_schedule_queries import connection, cursors, schedule_row
from test_service_api import PRIVATE, assert_safe


pytestmark = pytest.mark.usefixtures("forbid_database")
PATH = "/api/vehicles/8/maintenance-schedules"
DETAIL = f"{PATH}/12"
NOW = datetime(2020, 1, 1, tzinfo=UTC)
PUBLIC = {
    "id": 12, "vehicle_id": 8, "name": "Oil change", "interval_days": None,
    "interval_miles": "1000.0", "interval_hours": None, "baseline_date": None,
    "baseline_mileage": "0.0", "baseline_hours": None, "source_notes": None,
    "created_at": "2020-01-01T00:00:00Z",
}
CREATE = {"name": "Oil change", "interval_miles": "1000.0", "baseline_mileage": "0.0"}
PATCH = {"source_notes": None}


@pytest.fixture
def session(monkeypatch):
    actor = session_queries.AuthenticatedSession(
        RegistrationResponse(id=42, email="synthetic@example.com", created_at=NOW),
        1, NOW + timedelta(minutes=30),
    )
    validate = Mock(return_value=actor)
    monkeypatch.setattr(session_queries, "validate_and_extend_session", validate)
    return actor, validate


def mutate(client, method, **options):
    options.setdefault("headers", AUTH_HEADERS)
    if "json" not in options and "content" not in options:
        options["json"] = CREATE if method == "POST" else PATCH
    return client.request(method, PATH if method == "POST" else DETAIL, **options)


def assert_success(response, status, content, session):
    actor, validate = session
    assert response.status_code == status and response.json() == content
    assert response.headers["cache-control"] == "no-store"
    assert response.headers[authentication.SESSION_DEADLINE_HEADER] == actor.expires_at.isoformat()
    assert "set-cookie" not in response.headers
    validate.assert_called_once()


@pytest.mark.parametrize("rows", [[], [schedule_row(), schedule_row(15, "Brakes")]])
def test_get_returns_owned_schedules_without_csrf_headers(client, connection, session, rows):
    cursors(connection, schedules=rows)
    response = client.get(PATH + "?user_id=999")
    expected = [PUBLIC, {**PUBLIC, "id": 15, "name": "Brakes"}] if rows else []
    assert_success(response, 200, {"vehicle_id": 8, "schedules": expected}, session)
    database.connect_database.assert_called_once()
    assert database.connect_database.call_args.kwargs == {"read_only": True}
    assert [call.args[1] for call in connection.execute.call_args_list] == [(8, 42), (8, 42)]


@pytest.mark.parametrize("method,status", [("POST", 201), ("PATCH", 200)])
def test_mutations_return_the_saved_schedule_after_transaction_exit(client, connection, session, method, status):
    current_rows = [schedule_row(notes="Old notes")] if method == "PATCH" else []
    cursors(connection, schedules=current_rows, saved=schedule_row())
    response = mutate(client, method, headers={**AUTH_HEADERS, "Content-Type": "application/json; charset=utf-8"})
    assert_success(response, status, PUBLIC, session)
    write = connection.execute.call_args.args
    assert write[0].startswith("INSERT" if method == "POST" else "UPDATE")
    assert write[1][-2:] == (8, 42)
    connection.__exit__.assert_called_once_with(None, None, None)


@pytest.mark.parametrize("method,expected", [
    ("GET", "Vehicle not found."), ("POST", "Vehicle not found."),
    ("PATCH", "Maintenance schedule not found."),
])
def test_missing_and_foreign_have_indistinguishable_404s(client, connection, session, method, expected, caplog):
    responses = []
    for vehicle_id, owner_id in [(8, 42), (9, 43)]:
        actor, validate = session
        validate.return_value = session_queries.AuthenticatedSession(
            actor.user.model_copy(update={"id": owner_id}), actor.session_id, actor.expires_at,
        )
        connection.reset_mock()
        cursors(connection, parent=None)
        path = (DETAIL if method == "PATCH" else PATH).replace("/8/", f"/{vehicle_id}/")
        options = {} if method == "GET" else {"headers": AUTH_HEADERS, "json": CREATE if method == "POST" else PATCH}
        response = client.request(method, path, **options)
        assert_safe(response, 404, caplog)
        connection.execute.assert_called_once()
        assert connection.execute.call_args.args[1] == (vehicle_id, owner_id)
        responses.append(response.json())
    assert responses == [{"detail": expected}, {"detail": expected}]
    if method == "PATCH":
        cursors(connection, schedules=[])
        missing_schedule = mutate(client, method)
        assert_safe(missing_schedule, 404, caplog)
        assert missing_schedule.json() == responses[0]


@pytest.mark.parametrize("method", ["POST", "PATCH"])
@pytest.mark.parametrize("case", ["missing-origin", "untrusted-origin", "plain-text", "missing-marker", "duplicate-marker"])
def test_policy_denies_mutations_before_body_session_or_queries(client, session, monkeypatch, method, case, caplog):
    parse = AsyncMock(side_effect=AssertionError("The request body must remain unread"))
    monkeypatch.setattr(Request, "json", parse)
    response = mutate(client, method, headers=csrf_headers(case), content="{" + PRIVATE)
    assert_safe(response, 403, caplog)
    assert response.json() == {"detail": "Request not allowed."}
    parse.assert_not_awaited()
    session[1].assert_not_called()


@pytest.mark.parametrize("path,field", [
    (DETAIL.replace("/8/", "/08/"), "vehicle_id"),
    (f"{PATH}/%EF%BC%91", "schedule_id"),
    (f"{PATH}/2147483648", "schedule_id"),
    (f"{PATH}/{PRIVATE}", "schedule_id"),
])
def test_path_validation_does_not_echo_ids(client, session, connection, path, field, caplog):
    response = client.patch(path, headers=AUTH_HEADERS, json=PATCH)
    assert_safe(response, 422, caplog)
    assert response.json()["detail"][0]["loc"] == ["path", field]
    connection.execute.assert_not_called()


@pytest.mark.parametrize("method,body,location", [
    ("POST", {**CREATE, PRIVATE: PRIVATE}, ["body"]),
    ("POST", {**CREATE, "user_id": 999}, ["body"]),
    ("POST", {**CREATE, "interval_miles": PRIVATE}, ["body", "interval_miles"]),
    ("POST", {"name": PRIVATE, "interval_days": 30}, ["body", "baseline_date"]),
    ("POST", {**CREATE, "reviewed_duplicate_ids": [PRIVATE]}, ["body", "reviewed_duplicate_ids"]),
    ("PATCH", {}, ["body"]),
    ("PATCH", {"reviewed_duplicate_ids": [15]}, ["body"]),
    ("PATCH", {"source_notes": PRIVATE + "\u0000"}, ["body", "source_notes"]),
])
def test_validation_returns_only_allowlisted_fields_and_fixed_messages(
    client, session, connection, method, body, location, caplog,
):
    response = mutate(client, method, json=body)
    assert_safe(response, 422, caplog)
    details = response.json()["detail"]
    assert details[0]["loc"] == location
    assert all(set(error) == {"loc", "type", "msg"} for error in details)
    if not body or set(body) == {"reviewed_duplicate_ids"}:
        assert details[0]["msg"] == EMPTY_PATCH_ERROR
    connection.execute.assert_not_called()


@pytest.mark.parametrize("method", ["POST", "PATCH"])
@pytest.mark.parametrize("body", ["{" + PRIVATE, b"{\xff}", "[]"])
def test_malformed_or_non_object_request_body_is_safe(client, session, connection, method, body, caplog):
    response = mutate(client, method, content=body)
    assert_safe(response, 422, caplog)
    assert all(error["loc"] == ["body"] for error in response.json()["detail"])
    connection.execute.assert_not_called()


def test_invalid_merged_patch_returns_field_error_before_write(client, connection, session, caplog):
    cursors(connection, schedules=[schedule_row()])
    response = mutate(client, "PATCH", json={"baseline_mileage": None})
    assert_safe(response, 422, caplog)
    assert response.json()["detail"] == [{
        "loc": ["body", "baseline_mileage"], "type": "value_error",
        "msg": "Set both the mileage interval and its baseline, or clear both.",
    }]
    assert connection.execute.call_count == 2
    assert connection.__exit__.call_args.args[0] is not None


@pytest.mark.parametrize("method,status", [("POST", 201), ("PATCH", 200)])
def test_current_review_is_required_and_exact_before_write(client, connection, session, method, status, caplog):
    existing = [schedule_row()] if method == "PATCH" else []
    proposed = PATCH if method == "PATCH" else CREATE
    matches = [schedule_row(15), schedule_row(18)]
    for ids, current in [(None, matches[:1]), ([15], matches), ([15, 18], [])]:
        connection.reset_mock()
        cursors(connection, schedules=existing + current)
        body = proposed if ids is None else {**proposed, "reviewed_duplicate_ids": ids}
        response = mutate(client, method, json=body)
        assert_safe(response, 409, caplog)
        assert response.json() == {
            "code": "duplicate_schedule_name", "detail": DUPLICATE_NAME_DETAIL,
            "matches": [{**PUBLIC, "id": row[0]} for row in current],
        }
        assert connection.execute.call_count == 2
        assert connection.__exit__.call_args.args[0] is not None

    connection.reset_mock()
    session[1].reset_mock()
    saved = schedule_row(21) if method == "POST" else schedule_row()
    cursors(connection, schedules=existing + matches, saved=saved)
    accepted = mutate(client, method, json={**proposed, "reviewed_duplicate_ids": [18, 15]})
    assert_success(accepted, status, {**PUBLIC, "id": saved[0]}, session)
    assert connection.execute.call_count == 3
    assert "reviewed_duplicate_ids" not in connection.execute.call_args.args[0]


@pytest.mark.parametrize("stage,status,detail", [
    ("session rejected", 401, "Not authenticated."),
    ("authentication unavailable", 503, "Authentication unavailable. Please try again."),
    ("query unavailable", 503, "Maintenance schedules unavailable. Please try again."),
    ("commit unavailable", 503, "Maintenance schedules unavailable. Please try again."),
    ("invalid stored data", 500, "Internal server error"),
    ("unexpected", 500, "Internal server error"),
])
def test_error_responses_do_not_publish_private_details_or_prepared_success(
    client, session, connection, stage, status, detail, caplog,
):
    cursors(connection, schedules=[schedule_row()], saved=schedule_row())
    if stage == "session rejected":
        session[1].side_effect = session_queries.InvalidSessionError()
    elif stage == "authentication unavailable":
        session[1].side_effect = psycopg.OperationalError(PRIVATE)
    elif stage == "query unavailable":
        connection.execute.side_effect = psycopg.OperationalError(PRIVATE)
    elif stage == "commit unavailable":
        connection.__exit__.side_effect = psycopg.OperationalError(PRIVATE)
    elif stage == "invalid stored data":
        bad_row = (*schedule_row()[:4], PRIVATE, *schedule_row()[5:])
        cursors(connection, schedules=[bad_row])
    else:
        connection.execute.side_effect = RuntimeError(PRIVATE)
    response = mutate(client, "PATCH")
    assert_safe(response, status, caplog)
    assert response.json() == {"detail": detail}
    if stage == "session rejected":
        assert 'garageguide_session=""' in response.headers["set-cookie"]
    else:
        assert "set-cookie" not in response.headers
    if stage == "commit unavailable":
        connection.__exit__.assert_called_once_with(None, None, None)


def test_schedule_removal_is_not_exposed(client, connection, caplog):
    response = client.delete(DETAIL)
    assert_safe(response, 405, caplog)
    connection.execute.assert_not_called()
