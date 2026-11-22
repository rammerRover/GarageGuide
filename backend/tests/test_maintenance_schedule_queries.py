from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import psycopg
import pytest
from pydantic import ValidationError

from app import database, maintenance_schedule_queries as queries
from app.maintenance_schedule_schemas import MaintenanceScheduleCreate, MaintenanceSchedulePatch
from app.vehicle_queries import VehicleNotFoundError


pytestmark = pytest.mark.usefixtures("forbid_database")
ACTOR = SimpleNamespace(user=SimpleNamespace(id=42))
VEHICLE_ID = 8


def schedule_row(schedule_id=12, name="Oil change", *, notes=None):
    return (
        schedule_id, VEHICLE_ID, name, None, Decimal("1000.0"), None,
        None, Decimal("0.0"), None, notes, datetime(2020, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def connection(monkeypatch):
    conn = MagicMock()
    conn.__enter__.return_value = conn
    monkeypatch.setattr(database, "connect_database", Mock(return_value=conn))
    return conn


def cursors(connection, *, parent=(VEHICLE_ID,), schedules=(), saved=None):
    connection.execute.side_effect = [
        Mock(fetchone=Mock(return_value=parent)),
        Mock(fetchall=Mock(return_value=schedules)),
        Mock(fetchone=Mock(return_value=saved)),
    ]


def list_schedules():
    return queries.list_maintenance_schedules(None, actor=ACTOR, vehicle_id=VEHICLE_ID)


def create_request(**overrides):
    return MaintenanceScheduleCreate(**{
        "name": "Oil change", "interval_miles": "1000.0", "baseline_mileage": "0.0", **overrides,
    })


def create(**kwargs):
    return queries.create_maintenance_schedule(None, actor=ACTOR, vehicle_id=VEHICLE_ID, **kwargs)


def update(patch, **kwargs):
    return queries.update_maintenance_schedule(
        None, actor=ACTOR, vehicle_id=VEHICLE_ID, schedule_id=12, patch=patch, **kwargs,
    )


def test_owned_empty_list_uses_read_only_queries_scoped_to_vehicle_and_owner(connection):
    cursors(connection)
    assert list_schedules().model_dump() == {"vehicle_id": VEHICLE_ID, "schedules": []}
    database.connect_database.assert_called_once_with(None, read_only=True)
    parent, schedules = [call.args for call in connection.execute.call_args_list]
    assert "FOR UPDATE" not in parent[0]
    assert "WHERE m.vehicle_id = %s AND v.user_id = %s ORDER BY m.id" in schedules[0]
    assert parent[1] == schedules[1] == (VEHICLE_ID, ACTOR.user.id)


@pytest.mark.parametrize("operation", ["list", "create", "update"])
def test_unowned_parent_stops_after_scoped_lookup(connection, operation):
    cursors(connection, parent=None)
    with pytest.raises(VehicleNotFoundError):
        if operation == "list":
            list_schedules()
        elif operation == "create":
            create(schedule=create_request())
        else:
            update(MaintenanceSchedulePatch(source_notes=None))
    connection.execute.assert_called_once()
    assert connection.execute.call_args.args[1] == (VEHICLE_ID, ACTOR.user.id)
    assert connection.__exit__.call_args.args[0] is VehicleNotFoundError


def test_create_locks_first_binds_native_values_and_prepares_before_commit(connection):
    name = "Engineer’s task ' --"
    cursors(connection, saved=schedule_row(name=name, notes="Manual"))
    request = create_request(
        name=name, source_notes="Manual", interval_days=30, baseline_date="2020-02-29",
    )

    def prepare(result):
        connection.__exit__.assert_not_called()
        assert result.name == name
        assert result.model_dump(mode="json")["baseline_mileage"] == "0.0"

    assert create(schedule=request, prepare_response=prepare).name == name
    database.connect_database.assert_called_once_with(None, read_only=False)
    lock, read, write = [call.args for call in connection.execute.call_args_list]
    assert lock[0].endswith("AND user_id = %s FOR UPDATE")
    assert "ORDER BY m.id" in read[0]
    assert lock[1] == read[1] == (VEHICLE_ID, ACTOR.user.id)
    assert write[0].startswith("INSERT INTO public.maintenance_schedules ")
    assert "WHERE v.id = %s AND v.user_id = %s" in write[0] and name not in write[0]
    assert write[1] == (
        name, 30, Decimal("1000.0"), None, date(2020, 2, 29), Decimal("0.0"), None,
        "Manual", VEHICLE_ID, ACTOR.user.id,
    )
    connection.__exit__.assert_called_once_with(None, None, None)


def test_update_merges_locked_values_excludes_self_and_binds_all_scope_ids(connection):
    cursors(connection, schedules=[schedule_row(notes="Old draft")], saved=schedule_row())
    updated = update(MaintenanceSchedulePatch(source_notes=None))
    assert updated.source_notes is None
    lock, read, write = [call.args for call in connection.execute.call_args_list]
    assert lock[0].endswith("FOR UPDATE")
    assert lock[1] == read[1] == (VEHICLE_ID, ACTOR.user.id)
    assert write[0].startswith("UPDATE public.maintenance_schedules AS m ")
    assert "m.id = %s AND m.vehicle_id = %s" in write[0] and "v.user_id = %s" in write[0]
    assert write[1] == (
        "Oil change", None, Decimal("1000.0"), None, None, Decimal("0.0"), None, None,
        12, VEHICLE_ID, ACTOR.user.id,
    )


def test_update_missing_schedule_stops_without_unscoped_lookup(connection):
    cursors(connection)
    with pytest.raises(queries.MaintenanceScheduleNotFoundError):
        update(MaintenanceSchedulePatch(source_notes=None))
    assert connection.execute.call_count == 2


def test_invalid_merged_pair_rolls_back_before_write(connection):
    cursors(connection, schedules=[schedule_row()])
    with pytest.raises(ValidationError) as caught:
        update(MaintenanceSchedulePatch(baseline_mileage=None))
    assert caught.value.errors()[0]["loc"] == ("baseline_mileage",)
    assert connection.execute.call_count == 2
    assert connection.__exit__.call_args.args[0] is ValidationError


@pytest.mark.parametrize(("rows", "reviewed_ids", "matching_ids"), [
    ([schedule_row(12, "  Straße  "), schedule_row(16, "STRASSE")], None, [12, 16]),
    ([schedule_row(12, "  Straße  "), schedule_row(16, "STRASSE")], [12], [12, 16]),
    ([], [12], []),
])
def test_create_rejects_unreviewed_or_changed_matches(connection, rows, reviewed_ids, matching_ids):
    cursors(connection, schedules=rows)
    options = {} if reviewed_ids is None else {"reviewed_duplicate_ids": reviewed_ids}
    with pytest.raises(queries.DuplicateScheduleNameError) as caught:
        create(schedule=create_request(name="strasse", **options))
    assert caught.value.response.code == "duplicate_schedule_name"
    assert [schedule.id for schedule in caught.value.response.matches] == matching_ids
    assert connection.execute.call_count == 2
    assert connection.__exit__.call_args.args[0] is queries.DuplicateScheduleNameError


def test_update_conflict_matches_other_rows_only(connection):
    cursors(connection, schedules=[schedule_row(), schedule_row(16, "  OIL CHANGE  ")])
    with pytest.raises(queries.DuplicateScheduleNameError) as caught:
        update(MaintenanceSchedulePatch(source_notes="New"))
    assert [schedule.id for schedule in caught.value.response.matches] == [16]
    assert connection.execute.call_count == 2


def test_exact_reviewed_set_is_order_independent_and_is_never_bound(connection):
    cursors(connection, schedules=[schedule_row(), schedule_row(16)], saved=schedule_row(21))
    assert create(schedule=create_request(reviewed_duplicate_ids=[16, 12])).id == 21
    sql, params = connection.execute.call_args.args
    assert "reviewed_duplicate_ids" not in sql
    assert params[-2:] == (VEHICLE_ID, ACTOR.user.id)
    assert len(params) == 10


def test_database_failure_is_translated_after_transaction_exit_without_retry(connection):
    cursors(connection, saved=schedule_row())
    failure = psycopg.OperationalError("private detail")
    connection.__exit__.side_effect = failure
    with pytest.raises(queries.MaintenanceScheduleUnavailableError) as caught:
        create(schedule=create_request())
    assert "private detail" not in str(caught.value)
    assert caught.value.__suppress_context__
    assert connection.execute.call_count == 3
    connection.__exit__.assert_called_once()
