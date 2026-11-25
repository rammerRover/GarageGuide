from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import psycopg
import pytest

from app import database, maintenance_schedule_queries as queries, session_queries, vehicle_queries
from app.vehicle_schemas import VEHICLE_ID_ERROR
from test_maintenance_schedule_api import assert_success, session
from test_maintenance_schedule_queries import connection
from test_maintenance_status import NOW, TODAY, saved_schedule, saved_vehicle
from test_service_api import PRIVATE, assert_safe


pytestmark = pytest.mark.usefixtures("forbid_database")
PATH = "/api/vehicles/7/maintenance-schedules/status"


@pytest.fixture
def evaluation(monkeypatch):
    calendar = Mock(return_value=TODAY)
    clock = Mock(return_value=NOW)
    monkeypatch.setattr(queries, "get_current_date", calendar)
    monkeypatch.setattr(queries, "_current_instant", clock)
    return calendar, clock


def snapshot_rows(connection, vehicle, *schedules):
    prefix = tuple(getattr(vehicle, field) for field in vehicle_queries.PUBLIC_FIELDS)
    rows = (
        [prefix + tuple(getattr(task, field) for field in queries.PUBLIC_FIELDS) for task in schedules]
        if schedules else [prefix + (None,) * len(queries.PUBLIC_FIELDS)]
    )
    connection.execute.return_value.fetchall.return_value = rows


def test_query_reads_once_in_a_scoped_read_only_transaction_and_captures_time_once(connection, session, evaluation):
    actor, _ = session
    vehicle = saved_vehicle(mileage=Decimal("10.0"))
    tasks = [
        saved_schedule(id=12, interval_days=1, baseline_date=date(2026, 11, 23)),
        saved_schedule(id=13, interval_miles=Decimal("10.0"), baseline_mileage=Decimal("0.0")),
    ]
    snapshot_rows(connection, vehicle, *tasks)
    prepare = Mock()

    result = queries.get_maintenance_status(
        None, actor=actor, vehicle_id=vehicle.id, prepare_response=prepare,
    )

    assert result.vehicle == vehicle
    assert result.as_of_date == TODAY and result.readings_timestamp_warning is None
    assert [entry.schedule for entry in result.schedules] == tasks
    assert [entry.status for entry in result.schedules] == ["due", "due"]
    database.connect_database.assert_called_once_with(None, read_only=True)
    connection.execute.assert_called_once()
    sql, parameters = connection.execute.call_args.args
    assert sql.startswith("SELECT v.id, ") and sql.count("%s") == 2 and "FOR UPDATE" not in sql
    assert "LEFT JOIN public.maintenance_schedules AS m ON m.vehicle_id = v.id" in sql
    assert sql.endswith("WHERE v.id = %s AND v.user_id = %s ORDER BY m.id")
    assert parameters == (vehicle.id, actor.user.id)
    for source in evaluation:
        source.assert_called_once_with()
    prepare.assert_called_once_with(result)
    connection.__exit__.assert_called_once_with(None, None, None)


def test_owned_empty_status_returns_public_vehicle_and_empty_list(client, connection, session, evaluation):
    vehicle = saved_vehicle(mileage=Decimal("0.0"), readings_updated_at=None)
    snapshot_rows(connection, vehicle)
    response = client.get(PATH + "?user_id=999")
    assert_success(response, 200, {
        "vehicle": vehicle.model_dump(mode="json"), "as_of_date": TODAY.isoformat(),
        "readings_timestamp_warning": "missing", "schedules": [],
    }, session)
    assert connection.execute.call_args.args[1] == (vehicle.id, session[0].user.id)


def test_status_serializes_exact_decimal_results_and_overflow_calendar_fallback(client, connection, session, evaluation):
    maximum = Decimal("99999999999.9")
    vehicle = saved_vehicle(mileage=maximum, operating_hours=Decimal("2.1"))
    baseline = date(2020, 1, 1)
    task = saved_schedule(
        interval_days=2147483647, baseline_date=baseline,
        interval_miles=maximum, baseline_mileage=maximum,
        interval_hours=Decimal("0.2"), baseline_hours=Decimal("1.8"),
    )
    snapshot_rows(connection, vehicle, task)

    response = client.get(PATH)
    assert_success(response, 200, {
        "vehicle": vehicle.model_dump(mode="json"), "as_of_date": TODAY.isoformat(),
        "readings_timestamp_warning": None, "schedules": [{
            "schedule": task.model_dump(mode="json"), "status": "overdue", "limits": [
                {"kind": "days", "status": "upcoming", "due_value": None,
                 "remaining": 2147483647 - (TODAY - baseline).days, "issue": None},
                {"kind": "mileage", "status": "upcoming", "due_value": "199999999999.8",
                 "remaining": "99999999999.9", "issue": None},
                {"kind": "hours", "status": "overdue", "due_value": "2.0", "remaining": "-0.1", "issue": None},
            ],
        }],
    }, session)


def test_missing_and_foreign_statuses_are_identical(client, connection, session, evaluation, caplog):
    connection.execute.return_value.fetchall.return_value = []
    missing = client.get(PATH.replace("/7/", "/8/"))
    actor, validate = session
    validate.return_value = session_queries.AuthenticatedSession(
        actor.user.model_copy(update={"id": 43}), actor.session_id, actor.expires_at,
    )
    foreign = client.get(PATH)
    for response in (missing, foreign):
        assert_safe(response, 404, caplog)
        assert response.json() == {"detail": "Vehicle not found."}
    assert [call.args[1] for call in connection.execute.call_args_list] == [(8, 42), (7, 43)]
    for source in evaluation:
        source.assert_not_called()


@pytest.mark.parametrize("invalid_id", ["07", "2147483648", "%EF%BC%97", PRIVATE])
def test_invalid_status_path_is_sanitized(client, connection, session, invalid_id, caplog):
    response = client.get(PATH.replace("/7/", f"/{invalid_id}/"))
    assert_safe(response, 422, caplog)
    assert response.json() == {"detail": [{"loc": ["path", "vehicle_id"], "msg": VEHICLE_ID_ERROR, "type": "value_error"}]}
    connection.execute.assert_not_called()


def test_rejected_session_never_queries_the_vehicle_snapshot(client, connection, session, caplog):
    session[1].side_effect = session_queries.InvalidSessionError()
    response = client.get(PATH)
    assert_safe(response, 401, caplog)
    database.connect_database.assert_not_called()


@pytest.mark.parametrize(("stage", "status", "message"), [
    ("session", 503, "Authentication unavailable. Please try again."),
    ("query", 503, "Maintenance schedules unavailable. Please try again."),
    ("unexpected", 500, "Internal server error"),
])
def test_read_failures_return_safe_errors_without_a_deadline(client, connection, session, caplog, stage, status, message):
    if stage == "session":
        session[1].side_effect = psycopg.OperationalError(PRIVATE)
    elif stage == "query":
        connection.execute.side_effect = psycopg.OperationalError(PRIVATE)
    else:
        connection.execute.side_effect = RuntimeError(PRIVATE)

    response = client.get(PATH)
    assert_safe(response, status, caplog)
    assert response.json() == {"detail": message}
