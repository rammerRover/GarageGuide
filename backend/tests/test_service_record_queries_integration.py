from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from threading import Event
from time import monotonic

import psycopg
import pytest

from app import database, service_queries, vehicle_queries
from app.service_schemas import ServicePatch, ServiceRemovalRequest
from test_service_queries_integration import create_owned_service, owned_vehicle, reserved_service
from test_vehicle_queries_integration import actors


pytestmark = pytest.mark.integration


@pytest.fixture
def owned(native_database, actors):
    actor = actors[0]
    vehicle = owned_vehicle(native_database, actor)
    record = create_owned_service(native_database, actor, vehicle, reserved_service(
        native_database, actor, vehicle, mileage="500.0", operating_hours="5.0", cost="42.50", notes="Original notes",
    ))
    return vehicle, record


def read(native, actor, vehicle, record):
    return service_queries.get_service(native.settings, actor=actor, vehicle_id=vehicle.id, service_id=record.id)


def update(native, actor, vehicle, record, **fields):
    return service_queries.update_service(native.settings, actor=actor, vehicle_id=vehicle.id,
                                          service_id=record.id, patch=ServicePatch(**fields))


def remove(native, actor, vehicle, record, **options):
    return service_queries.remove_service(native.settings, actor=actor, vehicle_id=vehicle.id,
                                          service_id=record.id, confirmation=ServiceRemovalRequest(confirm_removal=True), **options)


def snapshot(native, actor, vehicle, record):
    with native.connect(native.settings, read_only=True) as connection:
        stored = connection.execute(
            "SELECT s.id, s.vehicle_id, s.service_date, s.service_type, s.description, s.mileage, "
            "s.operating_hours, s.cost, s.notes, s.created_at FROM public.service_records AS s "
            "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
            "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
            (record.id, vehicle.id, actor.user.id),
        ).fetchone()
        parts = connection.execute(
            "SELECT p.id, p.service_record_id, p.part_id, p.name, p.part_number, p.manufacturer, p.quantity, p.notes "
            "FROM public.service_parts AS p JOIN public.service_records AS s ON s.id = p.service_record_id "
            "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
            "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s ORDER BY p.id",
            (record.id, vehicle.id, actor.user.id),
        ).fetchall()
        completions = connection.execute(
            "SELECT c.id, c.vehicle_id, c.schedule_id, c.service_record_id, c.created_at "
            "FROM public.maintenance_completions AS c "
            "JOIN public.service_records AS s ON s.id = c.service_record_id AND s.vehicle_id = c.vehicle_id "
            "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
            "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s ORDER BY c.id",
            (record.id, vehicle.id, actor.user.id),
        ).fetchall()
        schedules = connection.execute(
            "SELECT m.id, m.vehicle_id, m.name, m.interval_days, m.interval_miles, m.interval_hours, "
            "m.baseline_date, m.baseline_mileage, m.baseline_hours, m.source_notes, m.created_at "
            "FROM public.maintenance_schedules AS m JOIN public.vehicles AS v ON v.id = m.vehicle_id "
            "WHERE m.vehicle_id = %s AND v.user_id = %s ORDER BY m.id", (vehicle.id, actor.user.id),
        ).fetchall()
    current_vehicle = vehicle_queries.get_vehicle(native.settings, actor=actor, vehicle_id=vehicle.id)
    return stored, parts, completions, schedules, current_vehicle


def reserve_link(native, actor, vehicle, record, kind):
    if kind == "part":
        return native.reserve_part_snapshot(record.id, vehicle.id, actor.user.id)
    name = native.reserve_maintenance_schedule(vehicle.id, actor.user.id)
    with native.connect(native.settings) as connection:
        schedule_id = connection.execute(
            "INSERT INTO public.maintenance_schedules (vehicle_id, name, interval_days, baseline_date) "
            "SELECT id, %s, %s, %s FROM public.vehicles WHERE id = %s AND user_id = %s RETURNING id",
            (name, 30, date(2020, 1, 1), vehicle.id, actor.user.id),
        ).fetchone()[0]
        native.remember_maintenance_schedule(schedule_id, vehicle.id, actor.user.id, name)
    native.reserve_maintenance_completion(schedule_id, record.id, vehicle.id, actor.user.id)
    return schedule_id


def insert_link(native, connection, actor, vehicle, record, kind, reservation):
    if kind == "part":
        snapshot_id = connection.execute(
            "INSERT INTO public.service_parts (service_record_id, name, quantity, notes) "
            "SELECT s.id, %s, %s, %s FROM public.service_records AS s "
            "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
            "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s RETURNING id",
            (reservation, 1, "Exact synthetic snapshot", record.id, vehicle.id, actor.user.id),
        ).fetchone()[0]
        native.remember_part_snapshot(snapshot_id, record.id, vehicle.id, actor.user.id, reservation)
        return snapshot_id
    return connection.execute(
        "INSERT INTO public.maintenance_completions (vehicle_id, schedule_id, service_record_id) "
        "SELECT s.vehicle_id, %s, s.id FROM public.service_records AS s "
        "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
        "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s RETURNING id",
        (reservation, record.id, vehicle.id, actor.user.id),
    ).fetchone()[0]


def add_link(native, actor, vehicle, record, kind):
    reservation = reserve_link(native, actor, vehicle, record, kind)
    with native.connect(native.settings) as connection:
        return insert_link(native, connection, actor, vehicle, record, kind, reservation)


def wait_for_blocker(locker, worker_pid):
    deadline = monotonic() + 1.5
    while monotonic() < deadline:
        if locker.execute("SELECT %s = ANY(pg_blocking_pids(%s))", (locker.info.backend_pid, worker_pid)).fetchone()[0]:
            return
        Event().wait(0.01)
    pytest.fail("PostgreSQL did not confirm the expected service/foreign-key lock wait", pytrace=False)


def test_detail_returns_complete_owned_public_record(native_database, actors, owned):
    vehicle, record = owned
    result = read(native_database, actors[0], vehicle, record)
    assert result == record and set(result.model_dump()) == set(service_queries.PUBLIC_FIELDS)


@pytest.mark.parametrize("operation", ["get", "update", "remove"])
def test_foreign_missing_and_wrong_parent_records_are_indistinguishable(native_database, actors, owned, operation):
    vehicle, record = owned
    other = owned_vehicle(native_database, actors[0])
    gone = create_owned_service(native_database, actors[0], other, reserved_service(native_database, actors[0], other))
    remove(native_database, actors[0], other, gone)
    outcomes = []
    for actor, parent, target in ((actors[1], vehicle, record), (actors[0], other, record), (actors[0], other, gone)):
        with pytest.raises(service_queries.ServiceNotFoundError) as caught:
            if operation == "get":
                read(native_database, actor, parent, target)
            elif operation == "update":
                update(native_database, actor, parent, target, notes="Must not apply")
            else:
                remove(native_database, actor, parent, target)
        outcomes.append((type(caught.value), caught.value.args))
    assert outcomes == [outcomes[0]] * 3
    assert read(native_database, actors[0], vehicle, record) == record


@pytest.mark.parametrize("fields", [
    {"service_date": "2019-01-01"}, {"service_type": "diagnostic"}, {"description": "Corrected' -- \u00e9"},
    {"notes": "  "}, {"mileage": "0.0"}, {"operating_hours": None}, {"cost": None},
    {"mileage": None, "operating_hours": "0", "cost": "0.00", "notes": None},
])
def test_edits_and_clears_commit_without_changing_vehicle_or_immutable_fields(native_database, actors, owned, fields):
    vehicle, record = owned
    actor = actors[0]
    before = snapshot(native_database, actor, vehicle, record)
    result = update(native_database, actor, vehicle, record, **fields)
    assert result == read(native_database, actor, vehicle, record)
    for name, value in ServicePatch(**fields).changes().items():
        assert getattr(result, name) == value
    assert (result.id, result.vehicle_id, result.created_at) == (record.id, vehicle.id, record.created_at)
    assert snapshot(native_database, actor, vehicle, record)[-1] == before[-1]


@pytest.mark.parametrize("links", [(), ("part",), ("completion",), ("part", "completion")])
def test_noop_saves_succeed_even_when_completion_linked(native_database, actors, owned, links):
    vehicle, record = owned
    actor = actors[0]
    for kind in links:
        add_link(native_database, actor, vehicle, record, kind)
    before = snapshot(native_database, actor, vehicle, record)
    assert update(native_database, actor, vehicle, record, cost="42.5", mileage="0500.0", description=record.description) == record
    assert snapshot(native_database, actor, vehicle, record) == before


@pytest.mark.parametrize("parts_also", [False, True])
@pytest.mark.parametrize("fields", [{"notes": "Must not apply"}, {"mileage": None, "operating_hours": "0"},
                                    {"service_date": "2019-01-01", "description": "No partial save", "cost": None}])
def test_completion_blocks_actual_edits_atomically_preserving_all_linked_data(native_database, actors, owned, parts_also, fields):
    vehicle, record = owned
    actor = actors[0]
    add_link(native_database, actor, vehicle, record, "completion")
    if parts_also:
        add_link(native_database, actor, vehicle, record, "part")
    before = snapshot(native_database, actor, vehicle, record)
    with pytest.raises(service_queries.ServiceEditBlockedError):
        update(native_database, actor, vehicle, record, **fields)
    assert snapshot(native_database, actor, vehicle, record) == before


def test_part_only_link_allows_edit_without_rewriting_snapshot(native_database, actors, owned):
    vehicle, record = owned
    actor = actors[0]
    add_link(native_database, actor, vehicle, record, "part")
    before = snapshot(native_database, actor, vehicle, record)
    result = update(native_database, actor, vehicle, record, notes="Corrected notes", mileage="1.0", cost=None)
    assert result.notes == "Corrected notes" and result.mileage == Decimal("1.0") and result.cost is None
    assert snapshot(native_database, actor, vehicle, record)[1:] == before[1:]


@pytest.mark.parametrize("links", [("part",), ("completion",), ("part", "completion")])
def test_linked_removal_leaves_service_children_schedule_and_vehicle_unchanged(native_database, actors, owned, links):
    vehicle, record = owned
    actor = actors[0]
    for kind in links:
        add_link(native_database, actor, vehicle, record, kind)
    before = snapshot(native_database, actor, vehicle, record)
    with pytest.raises(service_queries.ServiceRemovalBlockedError):
        remove(native_database, actor, vehicle, record)
    assert snapshot(native_database, actor, vehicle, record) == before


def test_removal_returns_only_after_preparation_commit_and_close(native_database, actors, owned, monkeypatch):
    vehicle, record = owned
    actor = actors[0]
    before = snapshot(native_database, actor, vehicle, record)
    opened, prepared = [], []
    @contextmanager
    def observe(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            if not read_only:
                opened.append(connection)
            yield connection
    def prepare(result):
        assert opened and not opened[-1].closed
        assert snapshot(native_database, actor, vehicle, record) == before
        prepared.append(result.model_dump())
    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", observe)
        result = remove(native_database, actor, vehicle, record, prepare_response=prepare)
    assert result.model_dump() == {"id": record.id, "vehicle_id": vehicle.id, "deleted": True}
    assert prepared == [result.model_dump()] and len(opened) == 1 and opened[0].closed
    with pytest.raises(service_queries.ServiceNotFoundError):
        read(native_database, actor, vehicle, record)
    assert snapshot(native_database, actor, vehicle, record)[1:] == before[1:]


def test_unrelated_edit_preserves_raw_omitted_legacy_date_and_description(native_database, actors, owned):
    vehicle, record = owned
    actor = actors[0]
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "UPDATE public.service_records AS s SET service_date = %s, description = %s FROM public.vehicles AS v "
            "WHERE s.id = %s AND s.vehicle_id = %s AND v.id = s.vehicle_id AND v.user_id = %s",
            (date(2099, 1, 1), "  Legacy description  ", record.id, vehicle.id, actor.user.id),
        )
    before = snapshot(native_database, actor, vehicle, record)
    result = update(native_database, actor, vehicle, record, notes="Unrelated edit")
    after = snapshot(native_database, actor, vehicle, record)
    assert result.service_date == date(2099, 1, 1)
    assert after[0][2] == date(2099, 1, 1) and after[0][4] == "  Legacy description  "
    assert after[1:] == before[1:]


def test_expense_view_tracks_known_unknown_and_removed_cost_without_duplicate_storage(native_database, actors, owned):
    vehicle, record = owned
    actor = actors[0]
    def expense():
        with native_database.connect(native_database.settings, read_only=True) as connection:
            return connection.execute(
                "SELECT service_count, recorded_total_usd, unknown_cost_count FROM public.vehicle_expense_summary "
                "WHERE vehicle_id = %s AND user_id = %s", (vehicle.id, actor.user.id),
            ).fetchone()
    assert expense() == (1, Decimal("42.50"), 0)
    update(native_database, actor, vehicle, record, cost=None)
    assert expense() == (1, Decimal("0"), 1)
    update(native_database, actor, vehicle, record, cost="0.00")
    assert expense() == (1, Decimal("0"), 0)
    remove(native_database, actor, vehicle, record)
    assert expense() == (0, Decimal("0"), 0)


@pytest.mark.parametrize("operation", ["get", "update", "remove"])
@pytest.mark.parametrize("failure_at", ["preparation", "pre-commit", "lost-ack"])
def test_real_transactions_rollback_known_failures_and_preserve_uncertain_outcomes(native_database, actors, owned, monkeypatch, operation, failure_at):
    vehicle, record = owned
    actor = actors[0]
    before = snapshot(native_database, actor, vehicle, record)
    opened = []
    @contextmanager
    def faulty(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection
            if failure_at == "pre-commit":
                raise psycopg.OperationalError("Synthetic failure before commit")
        if failure_at == "lost-ack":
            raise psycopg.OperationalError("Synthetic lost acknowledgment after real commit")
    def prepare(result):
        if failure_at == "preparation":
            raise RuntimeError("Synthetic preparation failure")
    options = {"actor": actor, "vehicle_id": vehicle.id, "service_id": record.id, "prepare_response": prepare}
    if operation == "update":
        options["patch"] = ServicePatch(notes="Committed correction")
    elif operation == "remove":
        options["confirmation"] = ServiceRemovalRequest(confirm_removal=True)
    function = getattr(service_queries, {"get": "get_service", "update": "update_service", "remove": "remove_service"}[operation])
    expected = RuntimeError if failure_at == "preparation" else service_queries.ServiceUnavailableError
    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", faulty)
        with pytest.raises(expected):
            function(native_database.settings, **options)
    assert len(opened) == 1 and opened[0].closed
    after = snapshot(native_database, actor, vehicle, record)
    if failure_at != "lost-ack" or operation == "get":
        assert after == before
    elif operation == "update":
        assert read(native_database, actor, vehicle, record).notes == "Committed correction"
        assert after[1:] == before[1:]
    else:
        assert after[0] is None and after[1:] == before[1:]


@pytest.mark.parametrize("overlap", [False, True])
def test_waiting_update_merges_latest_locked_omissions_and_supplied_values_win(native_database, actors, owned, monkeypatch, overlap):
    vehicle, record = owned
    actor = actors[0]
    ready, worker = Event(), []
    def worker_connect(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        worker.append(connection.info.backend_pid)
        ready.set()
        return connection
    fields = {"description": "Worker correction"}
    if overlap:
        fields["notes"] = "Worker notes"
    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", worker_connect)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with native_database.connect(native_database.settings) as locker:
                locker.execute(
                    "SELECT s.id FROM public.service_records AS s JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                    "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s FOR UPDATE OF s",
                    (record.id, vehicle.id, actor.user.id),
                )
                future = pool.submit(update, native_database, actor, vehicle, record, **fields)
                assert ready.wait(timeout=2)
                wait_for_blocker(locker, worker[0])
                locker.execute(
                    "UPDATE public.service_records AS s SET description = %s, notes = %s FROM public.vehicles AS v "
                    "WHERE s.id = %s AND s.vehicle_id = %s AND v.id = s.vehicle_id AND v.user_id = %s",
                    ("Locker correction", "Latest notes", record.id, vehicle.id, actor.user.id),
                )
            result = future.result(timeout=5)
    assert result.description == "Worker correction"
    assert result.notes == ("Worker notes" if overlap else "Latest notes")
    assert vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id) == vehicle


@pytest.mark.parametrize("kind", ["part", "completion"])
@pytest.mark.parametrize("operation", ["update", "remove"])
def test_child_insert_commits_first_and_waiting_mutation_rechecks_links(native_database, actors, owned, monkeypatch, kind, operation):
    vehicle, record = owned
    actor = actors[0]
    reservation = reserve_link(native_database, actor, vehicle, record, kind)
    before = snapshot(native_database, actor, vehicle, record)
    ready, worker = Event(), []
    def worker_connect(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        worker.append(connection.info.backend_pid)
        ready.set()
        return connection
    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", worker_connect)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with native_database.connect(native_database.settings) as inserter:
                child_id = insert_link(native_database, inserter, actor, vehicle, record, kind, reservation)
                future = pool.submit(remove if operation == "remove" else update, native_database, actor, vehicle, record,
                                     **({"notes": "Waiting correction"} if operation == "update" else {}))
                assert ready.wait(timeout=2)
                wait_for_blocker(inserter, worker[0])
            if operation == "update" and kind == "part":
                assert future.result(timeout=5).notes == "Waiting correction"
            else:
                expected = service_queries.ServiceRemovalBlockedError if operation == "remove" else service_queries.ServiceEditBlockedError
                with pytest.raises(expected):
                    future.result(timeout=5)
    after = snapshot(native_database, actor, vehicle, record)
    assert after[-1] == before[-1] and after[3] == before[3]
    assert (after[1] if kind == "part" else after[2])[0][0] == child_id
    if operation == "remove" or kind == "completion":
        assert after[0] == before[0]


@pytest.mark.parametrize("kind", ["part", "completion"])
def test_removal_commits_first_and_blocked_child_insert_cannot_commit(native_database, actors, owned, monkeypatch, kind):
    vehicle, record = owned
    actor = actors[0]
    reservation = reserve_link(native_database, actor, vehicle, record, kind)
    ready, worker, opened, future = Event(), [], [], []
    def attempt_insert():
        try:
            with native_database.connect(native_database.settings) as connection:
                worker.append(connection.info.backend_pid)
                ready.set()
                insert_link(native_database, connection, actor, vehicle, record, kind, reservation)
            return "unexpected-committed-child"
        except psycopg.errors.ForeignKeyViolation:
            return "foreign-key-rejected"
    @contextmanager
    def observe(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection
    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", observe)
        with ThreadPoolExecutor(max_workers=1) as pool:
            def prepare(result):
                future.append(pool.submit(attempt_insert))
                assert ready.wait(timeout=2)
                wait_for_blocker(opened[0], worker[0])
            result = remove(native_database, actor, vehicle, record, prepare_response=prepare)
            assert future[0].result(timeout=5) == "foreign-key-rejected"
    assert result.deleted is True and len(opened) == 1 and opened[0].closed
    assert service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id).services == []
    assert vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id) == vehicle


@pytest.mark.parametrize("operation", ["update", "remove"])
def test_real_lock_timeout_closes_and_translates_without_writes_or_retry(native_database, actors, owned, monkeypatch, operation):
    vehicle, record = owned
    actor = actors[0]
    ready, worker, opened = Event(), [], []
    def worker_connect(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        connection.execute("SET LOCAL lock_timeout = '1000ms'")
        opened.append(connection)
        worker.append(connection.info.backend_pid)
        ready.set()
        return connection
    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", worker_connect)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with native_database.connect(native_database.settings) as locker:
                locker.execute(
                    "SELECT s.id FROM public.service_records AS s JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                    "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s FOR UPDATE OF s",
                    (record.id, vehicle.id, actor.user.id),
                )
                future = pool.submit(remove if operation == "remove" else update, native_database, actor, vehicle, record,
                                     **({"notes": "Must not apply"} if operation == "update" else {}))
                assert ready.wait(timeout=2)
                wait_for_blocker(locker, worker[0])
                with pytest.raises(service_queries.ServiceUnavailableError):
                    future.result(timeout=4)
    assert len(opened) == 1 and opened[0].closed
    assert read(native_database, actor, vehicle, record) == record
