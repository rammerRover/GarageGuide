from datetime import date

import pytest

from app import database, maintenance_schedule_queries as queries, vehicle_queries
from test_maintenance_schedule_queries_integration import create, list_schedules
from test_service_api_integration import assert_headers
from test_vehicle_queries_integration import create_owned, reserved_vehicle
from test_vehicles_integration import accounts, install


pytestmark = pytest.mark.integration
TODAY = date(2026, 11, 24)


def status_path(vehicle_id):
    return f"/api/vehicles/{vehicle_id}/maintenance-schedules/status"


def test_native_empty_owned_snapshot_and_indistinguishable_denials(client, native_database, accounts, monkeypatch):
    owner, other = accounts
    actor = owner.session
    vehicle = create_owned(native_database, actor, reserved_vehicle(native_database, actor))
    monkeypatch.setattr(queries, "get_current_date", lambda: TODAY)
    install(client, owner)

    empty = client.get(status_path(vehicle.id))
    assert_headers(empty, 200, native_database, owner)
    assert empty.json() == {
        "vehicle": vehicle.model_dump(mode="json"), "as_of_date": TODAY.isoformat(),
        "readings_timestamp_warning": "missing", "schedules": [],
    }

    install(client, other)
    foreign = client.get(status_path(vehicle.id) + f"?user_id={actor.user.id}")
    missing = client.get(status_path(2147483647))
    for response in (foreign, missing):
        assert_headers(response, 404)
        assert response.json() == {"detail": "Vehicle not found."}
    assert list_schedules(native_database, actor, vehicle) == []
    assert vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id) == vehicle


def test_native_saved_limits_use_one_read_only_snapshot_and_leave_exact_rows_untouched(
    client, native_database, accounts, monkeypatch,
):
    owner = accounts[0]
    actor = owner.session
    vehicle = create_owned(native_database, actor, reserved_vehicle(
        native_database, actor, mileage="99999999999.9", operating_hours="2.1",
    ))
    baseline = date(2020, 1, 1)
    first = create(
        native_database, actor, vehicle, native_database.reserve_maintenance_schedule(vehicle.id, actor.user.id),
        interval_days=2147483647, baseline_date=baseline.isoformat(),
        interval_miles="99999999999.9", baseline_mileage="99999999999.9",
        interval_hours="0.2", baseline_hours="1.8",
    )
    second = create(
        native_database, actor, vehicle, native_database.reserve_maintenance_schedule(vehicle.id, actor.user.id),
        interval_days=(TODAY - baseline).days, baseline_date=baseline.isoformat(),
    )
    monkeypatch.setattr(queries, "get_current_date", lambda: TODAY)
    monkeypatch.setattr(queries, "_current_instant", lambda: vehicle.readings_updated_at)
    install(client, owner)

    guarded_connect = database.connect_database
    read_modes = []

    def observe_connection(settings, *, read_only):
        connection = guarded_connect(settings, read_only=read_only)
        if read_only:
            read_modes.append(connection.execute("SHOW transaction_read_only").fetchone())
        return connection

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", observe_connection)
        response = client.get(status_path(vehicle.id))

    assert_headers(response, 200, native_database, owner)
    assert read_modes == [("on",)]
    assert response.json() == {
        "vehicle": vehicle.model_dump(mode="json"), "as_of_date": TODAY.isoformat(),
        "readings_timestamp_warning": None, "schedules": [
            {"schedule": first.model_dump(mode="json"), "status": "overdue", "limits": [
                {"kind": "days", "status": "upcoming", "due_value": None,
                 "remaining": 2147483647 - (TODAY - baseline).days, "issue": None},
                {"kind": "mileage", "status": "upcoming", "due_value": "199999999999.8",
                 "remaining": "99999999999.9", "issue": None},
                {"kind": "hours", "status": "overdue", "due_value": "2.0", "remaining": "-0.1", "issue": None},
            ]},
            {"schedule": second.model_dump(mode="json"), "status": "due", "limits": [
                {"kind": "days", "status": "due", "due_value": TODAY.isoformat(), "remaining": 0, "issue": None},
            ]},
        ],
    }
    assert list_schedules(native_database, actor, vehicle) == [first, second]
    assert vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id) == vehicle
