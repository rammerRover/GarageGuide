from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from decimal import Decimal
from threading import Event
from time import monotonic

import psycopg
import pytest

from app import database, vehicle_queries
from app.vehicle_schemas import ReadingConfirmationRequired, VehiclePatch
from test_vehicle_queries_integration import actors, create_owned, reserved_vehicle


pytestmark = pytest.mark.integration


@pytest.fixture
def owned(native_database, actors):
    actor = actors[0]
    vehicle = create_owned(native_database, actor, reserved_vehicle(
        native_database, actor, mileage="1000.0", operating_hours="10.0", engine="V8",
    ))
    # The fixture finalizer was registered before account/session/vehicle writes.
    # Identity must be registered independently of all values before an edit.
    native_database.require_reserved_vehicle(vehicle.id, actor.user.id)
    return vehicle


def read(native, actor, vehicle_id):
    return vehicle_queries.get_vehicle(native.settings, actor=actor, vehicle_id=vehicle_id)


def update(native, actor, vehicle_id, **fields):
    native.require_reserved_vehicle(vehicle_id, actor.user.id)
    return vehicle_queries.update_vehicle(
        native.settings, actor=actor, vehicle_id=vehicle_id, patch=VehiclePatch.model_validate(fields),
    )


def test_detail_and_update_are_isolated_between_two_owners(native_database, actors, owned):
    first, second = actors
    assert read(native_database, first, owned.id) == owned
    other = create_owned(native_database, second, reserved_vehicle(native_database, second))
    assert read(native_database, second, other.id) == other
    for actor, foreign in [(second, owned), (first, other)]:
        with pytest.raises(vehicle_queries.VehicleNotFoundError, match="Vehicle not found"):
            read(native_database, actor, foreign.id)
        with pytest.raises(vehicle_queries.VehicleNotFoundError, match="Vehicle not found"):
            vehicle_queries.update_vehicle(
                native_database.settings, actor=actor, vehicle_id=foreign.id,
                patch=VehiclePatch(model="Must not apply"),
            )
    assert read(native_database, first, owned.id) == owned
    assert read(native_database, second, other.id) == other


@pytest.mark.parametrize("operation", ["get", "update"])
def test_deleted_missing_and_foreign_vehicle_have_identical_domain_outcome(native_database, actors, owned, operation):
    actor = actors[1]
    removed = create_owned(native_database, actor, reserved_vehicle(native_database, actor))
    with native_database.connect(native_database.settings) as connection:
        connection.execute("DELETE FROM public.vehicles WHERE id = %s AND user_id = %s", (removed.id, actor.user.id))
    results = []
    for vehicle_id in [removed.id, owned.id]:
        with pytest.raises(vehicle_queries.VehicleNotFoundError) as caught:
            if operation == "get":
                read(native_database, actor, vehicle_id)
            else:
                vehicle_queries.update_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle_id, patch=VehiclePatch(model="Must not apply"))
        results.append((type(caught.value), caught.value.args))
    assert results[0] == results[1]
    assert read(native_database, actors[0], owned.id) == owned


@pytest.mark.parametrize("fields", [{"make": "Synthetic' -- Updated"}, {"engine": None}, {"engine": "  "}, {"year": 1886}, {"vehicle_type": "Custom \U0001f6f5"}])
def test_text_edits_preserve_reading_time_creation_and_ownership(native_database, actors, owned, fields):
    result = update(native_database, actors[0], owned.id, **fields)
    assert result.readings_updated_at == owned.readings_updated_at
    assert result.created_at == owned.created_at and result.id == owned.id
    assert result == read(native_database, actors[0], owned.id)
    for name, value in VehiclePatch.model_validate(fields).changes().items():
        assert getattr(result, name) == value
    with native_database.connect(native_database.settings, read_only=True) as connection:
        assert connection.execute("SELECT user_id FROM public.vehicles WHERE id = %s AND user_id = %s", (owned.id, actors[0].user.id)).fetchone() == (actors[0].user.id,)


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("new", [None, "0.0", "2000.0"])
def test_real_reading_change_uses_postgresql_clock_and_commits(native_database, actors, owned, field, new):
    actor = actors[0]
    with native_database.connect(native_database.settings, read_only=True) as connection:
        before = connection.execute("SELECT clock_timestamp()").fetchone()[0]
    old = getattr(owned, field)
    result = update(native_database, actor, owned.id, **{
        field: new, "reading_confirmation": {field: format(old, ".1f")},
    })
    with native_database.connect(native_database.settings, read_only=True) as connection:
        after = connection.execute("SELECT clock_timestamp()").fetchone()[0]
    assert before <= result.readings_updated_at <= after
    assert result.readings_updated_at > owned.readings_updated_at
    assert getattr(result, field) == (None if new is None else Decimal(new))
    assert result.created_at == owned.created_at
    assert read(native_database, actor, owned.id) == result


def test_clearing_last_known_reading_records_time_and_null_to_zero_is_known(native_database, actors, owned):
    actor = actors[0]
    cleared = update(native_database, actor, owned.id, mileage=None, operating_hours=None,
                     reading_confirmation={"mileage": "1000", "operating_hours": "10"})
    assert cleared.mileage is None and cleared.operating_hours is None
    assert cleared.readings_updated_at is not None and cleared.readings_updated_at > owned.readings_updated_at
    zero = update(native_database, actor, owned.id, mileage="0")
    assert zero.mileage == Decimal("0.0") and zero.operating_hours is None
    assert zero.readings_updated_at > cleared.readings_updated_at


def test_missing_both_reading_confirmations_never_partially_writes(native_database, actors, owned):
    # Valid text is deliberately included to detect partial saves on rejection.
    fields = {"model": "No partial save"}
    with pytest.raises(ReadingConfirmationRequired) as caught:
        update(native_database, actors[0], owned.id, **fields, mileage=None, operating_hours="9")
    assert caught.value.fields == ("mileage", "operating_hours")
    assert read(native_database, actors[0], owned.id) == owned


def test_equal_values_are_noop_and_legacy_year_can_be_omitted(native_database, actors, owned):
    actor = actors[0]
    result = update(native_database, actor, owned.id, mileage="01000.0", operating_hours="10", make=owned.make)
    assert result == owned
    with native_database.connect(native_database.settings) as connection:
        connection.execute("UPDATE public.vehicles SET year = %s WHERE id = %s AND user_id = %s", (1, owned.id, actor.user.id))
    changed = update(native_database, actor, owned.id, model="Legacy edit")
    assert changed.year == 1 and changed.model == "Legacy edit"
    assert changed.readings_updated_at == owned.readings_updated_at


@pytest.mark.parametrize("fail_preparation", [False, True])
def test_public_preparation_precedes_commit_and_connections_close(native_database, actors, owned, monkeypatch, fail_preparation):
    opened = []

    @contextmanager
    def capture(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection

    def prepare(result):
        assert result.model == "Prepared update"
        assert not opened[0].closed
        # A distinct guarded physical connection must still see the old row.
        assert read(native_database, actors[0], owned.id).model == owned.model
        if fail_preparation:
            raise RuntimeError("Synthetic preparation failure")

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", capture)
        if fail_preparation:
            with pytest.raises(RuntimeError, match="Synthetic preparation failure"):
                vehicle_queries.update_vehicle(native_database.settings, actor=actors[0], vehicle_id=owned.id, patch=VehiclePatch(model="Prepared update"), prepare_response=prepare)
        else:
            result = vehicle_queries.update_vehicle(native_database.settings, actor=actors[0], vehicle_id=owned.id, patch=VehiclePatch(model="Prepared update"), prepare_response=prepare)
            assert result.model == "Prepared update"
    assert all(connection.closed for connection in opened)
    assert read(native_database, actors[0], owned.id).model == (owned.model if fail_preparation else "Prepared update")


def test_lost_commit_acknowledgment_is_uncertain_without_retry_and_exact_cleanup_still_works(native_database, actors, owned, monkeypatch):
    opened = []

    @contextmanager
    def lose_ack(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection
        raise psycopg.OperationalError("Synthetic acknowledgment lost after real commit")

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", lose_ack)
        with pytest.raises(vehicle_queries.VehicleUnavailableError):
            vehicle_queries.update_vehicle(native_database.settings, actor=actors[0], vehicle_id=owned.id, patch=VehiclePatch(model="Committed despite lost acknowledgment"))
    assert len(opened) == 1 and opened[0].closed
    assert read(native_database, actors[0], owned.id).model == "Committed despite lost acknowledgment"
    native_database.cleanup()
    assert native_database.cleanup_verified and native_database.cleanup_vehicle_count == 1
    assert native_database.cleanup_counts == (2, 2)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        assert connection.execute("SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s", (owned.id, actors[0].user.id)).fetchone() is None


def wait_for_blocker(locker, worker_pid):
    deadline = monotonic() + 1.5
    while monotonic() < deadline:
        if locker.execute("SELECT %s = ANY(pg_blocking_pids(%s))", (locker.info.backend_pid, worker_pid)).fetchone()[0]:
            return
        Event().wait(0.01)
    pytest.fail("PostgreSQL did not confirm the expected vehicle row-lock wait", pytrace=False)


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("replacement", ["1200.0", "800.0", None])
@pytest.mark.parametrize("proposed", ["900.0", None])
def test_waiting_update_rechecks_stale_confirmation_against_locked_latest_row(native_database, actors, owned, monkeypatch, field, replacement, proposed):
    actor = actors[0]
    old = getattr(owned, field)
    ready = Event()
    worker_pid = []

    def worker_connect(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        worker_pid.append(connection.info.backend_pid)
        ready.set()
        return connection

    def waiting_update():
        try:
            vehicle_queries.update_vehicle(native_database.settings, actor=actor, vehicle_id=owned.id,
                patch=VehiclePatch.model_validate({"model": "Must not apply", field: proposed,
                                                  "reading_confirmation": {field: format(old, ".1f")}}))
            return "unexpected-success"
        except ReadingConfirmationRequired as error:
            return error.fields, error.current_readings
        except Exception:
            return "unexpected-failure-redacted"

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", worker_connect)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with native_database.connect(native_database.settings) as locker:
                locker.execute("SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s FOR UPDATE", (owned.id, actor.user.id))
                future = pool.submit(waiting_update)
                assert ready.wait(timeout=2)
                wait_for_blocker(locker, worker_pid[0])
                # Identifier comes from this test's fixed parametrization, never input.
                assert field in ("mileage", "operating_hours")
                locker.execute(f"UPDATE public.vehicles SET {field} = %s, readings_updated_at = clock_timestamp() WHERE id = %s AND user_id = %s", (None if replacement is None else Decimal(replacement), owned.id, actor.user.id))
                expected_time = locker.execute("SELECT readings_updated_at FROM public.vehicles WHERE id = %s AND user_id = %s", (owned.id, actor.user.id)).fetchone()[0]
            required = replacement is not None and (proposed is None or Decimal(proposed) < Decimal(replacement))
            assert future.result(timeout=5) == (((field,), {field: replacement}) if required else ((), {}))
    final = read(native_database, actor, owned.id)
    assert final.model == owned.model and final.readings_updated_at == expected_time
    assert getattr(final, field) == (None if replacement is None else Decimal(replacement))


@pytest.mark.parametrize("reading_change", [False, True])
def test_waiting_update_merges_latest_omissions_and_samples_change_time_after_lock(native_database, actors, owned, monkeypatch, reading_change):
    actor = actors[0]
    ready = Event()
    worker = []

    def worker_connect(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        started = connection.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]
        worker.append((connection.info.backend_pid, started))
        ready.set()
        return connection

    fields = {"model": "Waiting update"}
    if reading_change:
        fields["mileage"] = "2000.0"
    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", worker_connect)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with native_database.connect(native_database.settings) as locker:
                locker.execute("SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s FOR UPDATE", (owned.id, actor.user.id))
                future = pool.submit(vehicle_queries.update_vehicle, native_database.settings, actor=actor, vehicle_id=owned.id, patch=VehiclePatch.model_validate(fields))
                assert ready.wait(timeout=2)
                wait_for_blocker(locker, worker[0][0])
                locker.execute("UPDATE public.vehicles SET make = %s, operating_hours = %s, readings_updated_at = clock_timestamp() WHERE id = %s AND user_id = %s", ("Latest concurrent make", Decimal("20.0"), owned.id, actor.user.id))
                previous_time, release_time = locker.execute("SELECT readings_updated_at, clock_timestamp() FROM public.vehicles WHERE id = %s AND user_id = %s", (owned.id, actor.user.id)).fetchone()
            result = future.result(timeout=5)
    assert result.make == "Latest concurrent make" and result.model == "Waiting update"
    assert result.operating_hours == Decimal("20.0") and result.created_at == owned.created_at
    if reading_change:
        assert result.mileage == Decimal("2000.0")
        assert result.readings_updated_at >= release_time > worker[0][1]
    else:
        assert result.readings_updated_at == previous_time
    assert read(native_database, actor, owned.id) == result


def test_actual_lock_timeout_translates_after_close_without_writes_or_retry(native_database, actors, owned, monkeypatch):
    ready = Event()
    worker = []
    opened = []

    def worker_connect(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        connection.execute("SET LOCAL lock_timeout = '1000ms'")
        opened.append(connection)
        worker.append(connection.info.backend_pid)
        ready.set()
        return connection

    def attempt():
        try:
            vehicle_queries.update_vehicle(native_database.settings, actor=actors[0], vehicle_id=owned.id, patch=VehiclePatch(model="Must not apply"))
        except vehicle_queries.VehicleUnavailableError as error:
            return str(error)
        return "unexpected-success"

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", worker_connect)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with native_database.connect(native_database.settings) as locker:
                locker.execute("SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s FOR UPDATE", (owned.id, actors[0].user.id))
                future = pool.submit(attempt)
                assert ready.wait(timeout=2)
                wait_for_blocker(locker, worker[0])
                assert future.result(timeout=5) == "Vehicles unavailable. Please try again."
    assert len(opened) == 1 and opened[0].closed
    assert read(native_database, actors[0], owned.id) == owned
