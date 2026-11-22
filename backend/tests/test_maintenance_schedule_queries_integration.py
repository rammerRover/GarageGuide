from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from app import database, maintenance_schedule_queries as queries, vehicle_queries
from app.maintenance_schedule_schemas import MaintenanceScheduleCreate, MaintenanceSchedulePatch
from test_service_queries_integration import owned_vehicle
from test_service_record_queries_integration import wait_for_blocker
from test_vehicle_queries_integration import actors


pytestmark = pytest.mark.integration


@pytest.fixture
def garage(native_database, actors):
    actor = actors[0]
    return actor, owned_vehicle(native_database, actor)


def list_schedules(native, actor, vehicle):
    return queries.list_maintenance_schedules(native.settings, actor=actor, vehicle_id=vehicle.id).schedules


def create(native, actor, vehicle, reserved_name, *, prepare=None, **values):
    request = MaintenanceScheduleCreate(**{
        "name": reserved_name, "interval_days": 30, "baseline_date": "2020-02-29", **values,
    })

    def capture(result):
        native.remember_maintenance_schedule(result.id, vehicle.id, actor.user.id, reserved_name)
        if prepare is not None:
            prepare(result)

    return queries.create_maintenance_schedule(
        native.settings, actor=actor, vehicle_id=vehicle.id, schedule=request, prepare_response=capture,
    )


def update(native, actor, vehicle, schedule, *, prepare=None, **values):
    return queries.update_maintenance_schedule(
        native.settings, actor=actor, vehicle_id=vehicle.id, schedule_id=schedule.id,
        patch=MaintenanceSchedulePatch(**values), prepare_response=prepare,
    )


def test_owned_empty_list_and_two_account_isolation(native_database, actors, garage):
    native = native_database
    owner, vehicle = garage
    other = actors[1]
    other_vehicle = owned_vehicle(native, other)
    assert list_schedules(native, owner, vehicle) == list_schedules(native, other, other_vehicle) == []
    name = native.reserve_maintenance_schedule(vehicle.id, owner.user.id)
    saved = create(native, owner, vehicle, name)
    for foreign_actor, foreign_vehicle in ((other, vehicle), (owner, other_vehicle)):
        with pytest.raises(vehicle_queries.VehicleNotFoundError):
            list_schedules(native, foreign_actor, foreign_vehicle)
        with pytest.raises(vehicle_queries.VehicleNotFoundError):
            queries.create_maintenance_schedule(
                native.settings, actor=foreign_actor, vehicle_id=foreign_vehicle.id,
                schedule=MaintenanceScheduleCreate(name=name, interval_days=1, baseline_date="2020-01-01"),
            )
        with pytest.raises(vehicle_queries.VehicleNotFoundError):
            update(native, foreign_actor, foreign_vehicle, saved, source_notes="Disallowed")
    with pytest.raises(queries.MaintenanceScheduleNotFoundError):
        update(native, other, other_vehicle, saved, source_notes="Wrong parent")
    assert list_schedules(native, owner, vehicle) == [saved]
    assert list_schedules(native, other, other_vehicle) == []


def test_write_and_rename_preserve_vehicle_readings_and_exact_values(native_database, garage):
    native = native_database
    actor, vehicle = garage
    name = native.reserve_maintenance_schedule(vehicle.id, actor.user.id)
    saved = create(
        native, actor, vehicle, name, interval_miles="1500.5", baseline_mileage="0.0",
        interval_hours="12.3", baseline_hours="5.4", source_notes="  Owner's reference  ",
    )
    renamed = update(
        native, actor, vehicle, saved, name=f"{name} revised",
        interval_days=None, baseline_date=None, source_notes=None,
    )
    public = renamed.model_dump(mode="json")
    assert public["interval_days"] is None and public["baseline_date"] is None
    assert public["baseline_mileage"] == "0.0"
    assert (public["interval_miles"], public["interval_hours"], public["baseline_hours"]) == ("1500.5", "12.3", "5.4")
    assert renamed.id == saved.id and renamed.created_at == saved.created_at
    assert list_schedules(native, actor, vehicle) == [renamed]
    assert vehicle_queries.get_vehicle(native.settings, actor=actor, vehicle_id=vehicle.id) == vehicle


def test_confirm_only_the_current_matching_ids_and_exclude_edited_schedule(native_database, garage):
    native = native_database
    actor, vehicle = garage
    name = native.reserve_maintenance_schedule(vehicle.id, actor.user.id)
    first = create(native, actor, vehicle, name)
    second = create(native, actor, vehicle, name, name=name.upper(), reviewed_duplicate_ids=[first.id])
    with pytest.raises(queries.DuplicateScheduleNameError) as stale:
        create(native, actor, vehicle, name, reviewed_duplicate_ids=[first.id])
    assert stale.value.response.matches == [first, second]
    with pytest.raises(queries.DuplicateScheduleNameError) as update_conflict:
        update(native, actor, vehicle, second, source_notes="New", reviewed_duplicate_ids=[first.id, second.id])
    assert update_conflict.value.response.matches == [first]
    new_second = update(native, actor, vehicle, second, source_notes="New", reviewed_duplicate_ids=[first.id])
    assert list_schedules(native, actor, vehicle) == [first, new_second]


def test_failed_response_preparation_rolls_back_insert_and_update(native_database, garage):
    native = native_database
    actor, vehicle = garage
    name = native.reserve_maintenance_schedule(vehicle.id, actor.user.id)

    def fail(result):
        raise RuntimeError("Test response preparation failed")

    with pytest.raises(RuntimeError, match="Test response preparation failed"):
        create(native, actor, vehicle, name, prepare=fail)
    assert list_schedules(native, actor, vehicle) == []
    saved = create(native, actor, vehicle, name)
    with pytest.raises(RuntimeError, match="Test response preparation failed"):
        update(native, actor, vehicle, saved, source_notes="Uncommitted", prepare=fail)
    assert list_schedules(native, actor, vehicle) == [saved]


@pytest.mark.parametrize("waiting_write", ["create", "update"])
def test_waiting_save_rechecks_matches_after_lock_holder_commits(native_database, garage, monkeypatch, waiting_write):
    native = native_database
    actor, vehicle = garage
    name = native.reserve_maintenance_schedule(vehicle.id, actor.user.id)
    original = None
    if waiting_write == "update":
        original = create(native, actor, vehicle, native.reserve_maintenance_schedule(vehicle.id, actor.user.id))
    opened, submitted, ready = [], [], Event()

    def observe(settings, *, read_only):
        connection = native.connect(settings, read_only=read_only)
        opened.append(connection)
        if len(opened) == 2:
            ready.set()
        return connection

    def save_again():
        if waiting_write == "create":
            return create(native, actor, vehicle, name, name=name.upper())
        return update(native, actor, vehicle, original, name=name.upper())

    with monkeypatch.context() as patches, ThreadPoolExecutor(max_workers=1) as pool:
        patches.setattr(database, "connect_database", observe)

        def hold_until_waiting(result):
            submitted.append(pool.submit(save_again))
            assert ready.wait(timeout=2)
            wait_for_blocker(opened[0], opened[1].info.backend_pid)

        first = create(native, actor, vehicle, name, prepare=hold_until_waiting)
        with pytest.raises(queries.DuplicateScheduleNameError) as caught:
            submitted[0].result(timeout=5)
    assert caught.value.response.matches == [first]
    assert all(connection.closed for connection in opened)
    assert list_schedules(native, actor, vehicle) == ([first] if original is None else [original, first])
