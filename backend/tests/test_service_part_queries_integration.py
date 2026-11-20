from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Event

import psycopg
import pytest

from app import database, service_part_queries as queries, service_queries, vehicle_queries
from app.service_part_schemas import (
    CatalogPartLookup, CatalogPartPreview, CatalogServicePartCreate, ManualServicePartCreate,
    ServicePartRemovalRequest,
)
from app.service_queries import ServiceNotFoundError
from app.service_schemas import ServiceRemovalRequest
from app.vehicle_queries import VehicleNotFoundError
from test_service_queries_integration import create_owned_service, owned_vehicle, reserved_service
from test_service_record_queries_integration import owned, wait_for_blocker
from test_vehicle_queries_integration import actors


pytestmark = pytest.mark.integration


def create_catalog(native):
    fields = native.reserve_catalog_part()
    with native.connect(native.settings) as connection:
        row = connection.execute(
            "INSERT INTO public.parts (manufacturer, part_number, name, category) VALUES (%s, %s, %s, %s) "
            "RETURNING id, manufacturer, part_number, name, category",
            tuple(fields[key] for key in ("manufacturer", "part_number", "name", "category")),
        ).fetchone()
    result = CatalogPartPreview(**dict(zip(queries.CATALOG_FIELDS, row, strict=True)))
    native.track_catalog_part(result.id, result.manufacturer, result.part_number)
    return result


def manual(native, actor, vehicle, record, **values):
    name = native.reserve_part_snapshot(record.id, vehicle.id, actor.user.id)
    return ManualServicePartCreate(source="manual", name=name, **values)


def catalog_request(native, actor, vehicle, record, preview, **values):
    native.reserve_part_snapshot(record.id, vehicle.id, actor.user.id, name=preview.name)
    return CatalogServicePartCreate(source="catalog", preview=preview, **values)


def attach(native, actor, vehicle, record, request, **options):
    prepare_response = options.pop("prepare_response", None)
    def prepare(result):
        native.remember_part_snapshot(result.id, record.id, vehicle.id, actor.user.id, result.name)
        if prepare_response is not None:
            prepare_response(result)
    result = queries.attach_service_part(native.settings, actor=actor, vehicle_id=vehicle.id,
                                         service_id=record.id, part=request, prepare_response=prepare, **options)
    native.track_part_snapshot(result.id, record.id, vehicle.id, actor.user.id, result.name)
    return result


def listing(native, actor, vehicle, record):
    return queries.list_service_parts(native.settings, actor=actor, vehicle_id=vehicle.id, service_id=record.id)


def lookup(native, actor, vehicle, record, preview):
    return queries.lookup_catalog_part(native.settings, actor=actor, vehicle_id=vehicle.id, service_id=record.id,
                                       lookup=CatalogPartLookup(manufacturer=preview.manufacturer, part_number=preview.part_number))


def removal(native, actor, vehicle, record, part, **options):
    return queries.remove_service_part(native.settings, actor=actor, vehicle_id=vehicle.id,
                                       service_id=record.id, snapshot_id=part.id,
                                       confirmation=ServicePartRemovalRequest(confirm_removal=True), **options)


def parent_state(native, actor, vehicle, record):
    return (
        vehicle_queries.get_vehicle(native.settings, actor=actor, vehicle_id=vehicle.id),
        service_queries.get_service(native.settings, actor=actor, vehicle_id=vehicle.id, service_id=record.id),
    )


@pytest.mark.parametrize("quantity,optional", [(None, None), (1, ""), (2147483647, "0")])
def test_manual_snapshot_exact_values_and_order_without_catalog_dependency(native_database, actors, owned, quantity, optional):
    vehicle, record = owned
    actor = actors[0]
    before = parent_state(native_database, actor, vehicle, record)
    assert listing(native_database, actor, vehicle, record).parts == []
    fields = {"manufacturer": optional, "part_number": optional, "notes": optional}
    if quantity is not None:
        fields["quantity"] = quantity
    request = manual(native_database, actor, vehicle, record, **fields)
    first = attach(native_database, actor, vehicle, record, request)
    second = attach(native_database, actor, vehicle, record, request)
    assert first.id < second.id
    assert listing(native_database, actor, vehicle, record).parts == [first, second]
    assert first.quantity == (quantity if quantity is not None else 1)
    assert first.part_number == first.manufacturer == first.notes == (optional or None)
    assert first.part_id is None
    assert set(first.model_dump(mode="json")) == set(queries.PUBLIC_FIELDS)
    assert parent_state(native_database, actor, vehicle, record) == before


def test_catalog_lookup_is_exact_case_sensitive_and_preserves_input(native_database, actors, owned):
    vehicle, record = owned
    actor = actors[0]
    catalog = create_catalog(native_database)
    assert lookup(native_database, actor, vehicle, record, catalog) == catalog
    for field, value in [("manufacturer", catalog.manufacturer.upper()),
                         ("part_number", catalog.part_number.upper()),
                         ("manufacturer", " " + catalog.manufacturer),
                         ("part_number", catalog.part_number + " ")]:
        changed = catalog.model_copy(update={field: value})
        with pytest.raises(queries.CatalogPartNotFoundError):
            lookup(native_database, actor, vehicle, record, changed)
    assert listing(native_database, actor, vehicle, record).parts == []


def test_catalog_attachment_copies_identity_and_removal_leaves_catalog_and_parents(native_database, actors, owned):
    vehicle, record = owned
    actor = actors[0]
    before = parent_state(native_database, actor, vehicle, record)
    catalog = create_catalog(native_database)
    request = catalog_request(native_database, actor, vehicle, record, catalog, notes="\ufeffHistorical note\ufeff")
    saved = attach(native_database, actor, vehicle, record, request)
    assert (saved.part_id, saved.name, saved.part_number, saved.manufacturer) == (
        catalog.id, catalog.name, catalog.part_number, catalog.manufacturer)
    assert saved.quantity == 1 and saved.notes == request.notes
    removed = removal(native_database, actor, vehicle, record, saved)
    assert removed.model_dump(mode="json") == {"id": saved.id, "service_record_id": record.id, "deleted": True}
    assert lookup(native_database, actor, vehicle, record, catalog) == catalog
    assert parent_state(native_database, actor, vehicle, record) == before
    assert listing(native_database, actor, vehicle, record).parts == []
    with pytest.raises(queries.ServicePartNotFoundError):
        removal(native_database, actor, vehicle, record, saved)


@pytest.mark.parametrize("change", ["edit", "delete"])
def test_saved_snapshot_is_historical_after_catalog_edit_or_deletion(native_database, actors, owned, change):
    vehicle, record = owned
    actor = actors[0]
    catalog = create_catalog(native_database)
    before = parent_state(native_database, actor, vehicle, record)
    saved = attach(native_database, actor, vehicle, record, catalog_request(native_database, actor, vehicle, record, catalog))
    with native_database.connect(native_database.settings) as connection:
        if change == "edit":
            connection.execute(
                "UPDATE public.parts SET manufacturer = %s, part_number = %s, name = %s, category = %s WHERE id = %s",
                (catalog.manufacturer + " edited", catalog.part_number + " edited", catalog.name + " edited", "Edited synthetic", catalog.id),
            )
        else:
            connection.execute("DELETE FROM public.parts WHERE id = %s", (catalog.id,))
    current = listing(native_database, actor, vehicle, record).parts
    expected = saved if change == "edit" else saved.model_copy(update={"part_id": None})
    assert current == [expected]
    assert parent_state(native_database, actor, vehicle, record) == before


@pytest.mark.parametrize("change", ["manufacturer", "part_number", "name", "category", "delete", "replace"])
def test_changed_disappeared_or_replaced_preview_writes_nothing(native_database, actors, owned, change):
    vehicle, record = owned
    actor = actors[0]
    catalog = create_catalog(native_database)
    request = catalog_request(native_database, actor, vehicle, record, catalog)
    before = parent_state(native_database, actor, vehicle, record)
    replacement = None
    with native_database.connect(native_database.settings) as connection:
        if change in {"delete", "replace"}:
            connection.execute("DELETE FROM public.parts WHERE id = %s", (catalog.id,))
            if change == "replace":
                replacement = connection.execute(
                    "INSERT INTO public.parts (manufacturer, part_number, name, category) VALUES (%s, %s, %s, %s) RETURNING id",
                    (catalog.manufacturer, catalog.part_number, catalog.name, catalog.category),
                ).fetchone()[0]
        else:
            # The identifier is selected only from this fixed test parameter set.
            connection.execute(f"UPDATE public.parts SET {change} = %s WHERE id = %s", (getattr(catalog, change) + " changed", catalog.id))
    if replacement is not None:
        native_database.track_catalog_part(replacement, catalog.manufacturer, catalog.part_number)
        assert replacement != catalog.id
    with pytest.raises(queries.CatalogPreviewConflictError):
        attach(native_database, actor, vehicle, record, request)
    assert listing(native_database, actor, vehicle, record).parts == []
    assert parent_state(native_database, actor, vehicle, record) == before


@pytest.mark.parametrize("operation", ["list", "lookup", "manual", "catalog", "remove"])
def test_every_operation_scopes_owner_vehicle_and_service(native_database, actors, owned, operation):
    vehicle, record = owned
    actor, other = actors
    foreign_vehicle = owned_vehicle(native_database, other)
    foreign = create_owned_service(native_database, other, foreign_vehicle,
                                   reserved_service(native_database, other, foreign_vehicle))
    missing = create_owned_service(native_database, actor, vehicle, reserved_service(native_database, actor, vehicle))
    service_queries.remove_service(native_database.settings, actor=actor, vehicle_id=vehicle.id,
                                    service_id=missing.id, confirmation=ServiceRemovalRequest(confirm_removal=True))
    other_vehicle = owned_vehicle(native_database, actor)
    catalog = create_catalog(native_database)
    saved = attach(native_database, actor, vehicle, record, manual(native_database, actor, vehicle, record))
    request = catalog_request(native_database, actor, vehicle, record, catalog) if operation == "catalog" else manual(native_database, actor, vehicle, record)
    def call(vid, sid, user=actor):
        options = {"actor": user, "vehicle_id": vid, "service_id": sid}
        if operation == "list":
            return queries.list_service_parts(native_database.settings, **options)
        if operation == "lookup":
            return queries.lookup_catalog_part(native_database.settings,
                lookup=CatalogPartLookup(manufacturer=catalog.manufacturer, part_number=catalog.part_number), **options)
        if operation == "remove":
            return queries.remove_service_part(native_database.settings, snapshot_id=saved.id,
                confirmation=ServicePartRemovalRequest(confirm_removal=True), **options)
        return queries.attach_service_part(native_database.settings, part=request, **options)
    for vid, sid, user, error in [
        (foreign_vehicle.id, foreign.id, actor, VehicleNotFoundError),
        (vehicle.id, record.id, other, VehicleNotFoundError),
        (vehicle.id, foreign.id, actor, ServiceNotFoundError),
        (other_vehicle.id, record.id, actor, ServiceNotFoundError),
        (vehicle.id, missing.id, actor, ServiceNotFoundError),
    ]:
        with pytest.raises(error):
            call(vid, sid, user)
    assert listing(native_database, actor, vehicle, record).parts == [saved]
    assert listing(native_database, other, foreign_vehicle, foreign).parts == []
    if operation == "remove":
        with pytest.raises(queries.ServicePartNotFoundError):
            call(foreign_vehicle.id, foreign.id, other)


@pytest.mark.parametrize("operation", ["manual", "catalog", "remove"])
@pytest.mark.parametrize("failure", ["prepare", "pre-commit", "lost-ack"])
def test_native_rollback_closure_and_uncertain_commit_recovery(native_database, actors, owned, monkeypatch, operation, failure):
    vehicle, record = owned
    actor = actors[0]
    catalog = create_catalog(native_database) if operation == "catalog" else None
    request = catalog_request(native_database, actor, vehicle, record, catalog) if catalog else manual(native_database, actor, vehicle, record)
    original = attach(native_database, actor, vehicle, record, request) if operation == "remove" else None
    before = parent_state(native_database, actor, vehicle, record)
    opened = []
    @contextmanager
    def faulty(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            opened.append(connection)
            yield connection
            if failure == "pre-commit":
                raise psycopg.OperationalError("Synthetic before-commit failure")
        if failure == "lost-ack":
            raise psycopg.OperationalError("Synthetic lost acknowledgment after real commit")
    def prepare(result):
        if failure == "prepare":
            raise RuntimeError("Synthetic response preparation failure")
    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", faulty)
        with pytest.raises(RuntimeError if failure == "prepare" else queries.ServicePartsUnavailableError):
            if original:
                removal(native_database, actor, vehicle, record, original, prepare_response=prepare)
            else:
                attach(native_database, actor, vehicle, record, request, prepare_response=prepare)
    assert len(opened) == 1 and opened[0].closed
    assert parent_state(native_database, actor, vehicle, record) == before
    count = len(listing(native_database, actor, vehicle, record).parts)
    assert count == (int(failure != "lost-ack") if operation == "remove" else int(failure == "lost-ack"))
    if failure == "lost-ack":
        # The pre-commit callback retained the exact ID despite the lost return.
        native_database.cleanup()
        assert native_database.cleanup_verified
        assert native_database.cleanup_link_counts[0] >= 1


def test_attachment_commits_first_and_waiting_service_removal_is_blocked(native_database, actors, owned, monkeypatch):
    vehicle, record = owned
    actor = actors[0]
    request = manual(native_database, actor, vehicle, record)
    ready, opened, future = Event(), [], []
    def observe(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        opened.append(connection)
        if len(opened) > 1:
            ready.set()
        return connection
    with monkeypatch.context() as patches, ThreadPoolExecutor(max_workers=1) as pool:
        patches.setattr(database, "connect_database", observe)
        def prepare(result):
            future.append(pool.submit(service_queries.remove_service, native_database.settings,
                actor=actor, vehicle_id=vehicle.id, service_id=record.id,
                confirmation=ServiceRemovalRequest(confirm_removal=True)))
            assert ready.wait(timeout=2)
            wait_for_blocker(opened[0], opened[1].info.backend_pid)
        saved = attach(native_database, actor, vehicle, record, request, prepare_response=prepare)
        with pytest.raises(service_queries.ServiceRemovalBlockedError):
            future[0].result(timeout=5)
    assert all(connection.closed for connection in opened)
    assert listing(native_database, actor, vehicle, record).parts == [saved]
    assert service_queries.get_service(native_database.settings, actor=actor, vehicle_id=vehicle.id, service_id=record.id) == record


def test_service_removal_commits_first_and_waiting_attachment_writes_nothing(native_database, actors, owned, monkeypatch):
    vehicle, record = owned
    actor = actors[0]
    request = manual(native_database, actor, vehicle, record)
    ready, opened, future = Event(), [], []
    def observe(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        opened.append(connection)
        if len(opened) > 1:
            ready.set()
        return connection
    with monkeypatch.context() as patches, ThreadPoolExecutor(max_workers=1) as pool:
        patches.setattr(database, "connect_database", observe)
        def prepare(result):
            future.append(pool.submit(attach, native_database, actor, vehicle, record, request))
            assert ready.wait(timeout=2)
            wait_for_blocker(opened[0], opened[1].info.backend_pid)
        removed = service_queries.remove_service(native_database.settings, actor=actor, vehicle_id=vehicle.id,
            service_id=record.id, confirmation=ServiceRemovalRequest(confirm_removal=True), prepare_response=prepare)
        with pytest.raises(ServiceNotFoundError):
            future[0].result(timeout=5)
    assert removed.deleted and all(connection.closed for connection in opened)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        assert connection.execute("SELECT id FROM public.service_parts WHERE service_record_id = %s", (record.id,)).fetchall() == []
    assert vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id) == vehicle


def test_catalog_identity_cannot_change_between_comparison_and_commit(native_database, actors, owned, monkeypatch):
    vehicle, record = owned
    actor = actors[0]
    catalog = create_catalog(native_database)
    request = catalog_request(native_database, actor, vehicle, record, catalog)
    ready, updater, future, holder = Event(), [], [], []
    def observe(settings, *, read_only):
        connection = native_database.connect(settings, read_only=read_only)
        holder.append(connection)
        return connection
    def update_catalog():
        with native_database.connect(native_database.settings) as connection:
            updater.append(connection)
            ready.set()
            connection.execute("UPDATE public.parts SET name = %s WHERE id = %s", (catalog.name + " changed", catalog.id))
    with monkeypatch.context() as patches, ThreadPoolExecutor(max_workers=1) as pool:
        patches.setattr(database, "connect_database", observe)
        def prepare(result):
            future.append(pool.submit(update_catalog))
            assert ready.wait(timeout=2)
            wait_for_blocker(holder[0], updater[0].info.backend_pid)
        saved = attach(native_database, actor, vehicle, record, request, prepare_response=prepare)
        future[0].result(timeout=5)
    assert saved.name == catalog.name
    assert listing(native_database, actor, vehicle, record).parts == [saved]
