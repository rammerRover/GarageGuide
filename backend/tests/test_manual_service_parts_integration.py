from types import SimpleNamespace

import pytest

from app import service_part_queries
from database_support import TestDatabaseSafetyError
from test_service_part_queries_integration import attach, catalog_request, listing, parent_state
from test_service_record_queries_integration import owned
from test_vehicle_queries_integration import actors
import manual_registration_server as manual


pytestmark = pytest.mark.integration


def controller(native):
    return SimpleNamespace(state=SimpleNamespace(browser_catalog={"native": native, "settings": native.settings, "preview": None}))


def test_guarded_terminal_catalog_lifecycle_preserves_snapshots_and_stale_preview_conflicts(native_database, actors, owned):
    vehicle, record = owned
    actor = actors[0]
    application = controller(native_database)
    original = manual.browser_catalog_command(application, "create")
    before = parent_state(native_database, actor, vehicle, record)
    request = catalog_request(native_database, actor, vehicle, record, original)
    saved = attach(native_database, actor, vehicle, record, request)
    assert native_database.require_reserved_parts(record.id, vehicle.id, actor.user.id)
    changed = manual.browser_catalog_command(application, "change")
    assert changed.id == original.id and changed.name != original.name
    with pytest.raises(service_part_queries.CatalogPreviewConflictError):
        attach(native_database, actor, vehicle, record, request)
    assert listing(native_database, actor, vehicle, record).parts == [saved]
    replaced = manual.browser_catalog_command(application, "replace")
    assert replaced.id != changed.id and replaced.part_number == changed.part_number
    assert listing(native_database, actor, vehicle, record).parts == [saved.model_copy(update={"part_id": None})]
    new_request = catalog_request(native_database, actor, vehicle, record, replaced)
    second = attach(native_database, actor, vehicle, record, new_request)
    manual.browser_catalog_command(application, "delete")
    assert listing(native_database, actor, vehicle, record).parts == [saved.model_copy(update={"part_id": None}), second.model_copy(update={"part_id": None})]
    assert parent_state(native_database, actor, vehicle, record) == before


def test_guarded_catalog_delete_refuses_untracked_reference_without_changing_data(native_database, actors, owned):
    vehicle, record = owned
    actor = actors[0]
    application = controller(native_database)
    preview = manual.browser_catalog_command(application, "create")
    saved = attach(native_database, actor, vehicle, record, catalog_request(native_database, actor, vehicle, record, preview))
    reservation = native_database._parts.pop(saved.id)
    try:
        with pytest.raises(TestDatabaseSafetyError, match="untracked snapshot"):
            manual.browser_catalog_command(application, "delete")
    finally:
        native_database._parts[saved.id] = reservation
    assert listing(native_database, actor, vehicle, record).parts == [saved]
    assert native_database.require_reserved_catalog_pair(preview.manufacturer, preview.part_number)


def test_untracked_same_name_snapshot_blocks_guard_and_cleanup_without_deletion(native_database, actors, owned):
    from test_service_part_queries_integration import manual as manual_request
    vehicle, record = owned
    actor = actors[0]
    request = manual_request(native_database, actor, vehicle, record)
    first = attach(native_database, actor, vehicle, record, request)
    second = attach(native_database, actor, vehicle, record, request)
    before = parent_state(native_database, actor, vehicle, record)
    # Both IDs belong to this test. Hide one only to exercise refusal of an
    # unknown row, and restore it even on failure so final teardown stays exact.
    reservation = native_database._parts.pop(second.id)
    try:
        with pytest.raises(TestDatabaseSafetyError, match="synthetic part"):
            native_database.require_reserved_parts(record.id, vehicle.id, actor.user.id)
        with pytest.raises(TestDatabaseSafetyError, match="Unexpected snapshot ID"):
            native_database.cleanup()
        assert native_database._parts == {first.id: reservation}
        assert listing(native_database, actor, vehicle, record).parts == [first, second]
        assert parent_state(native_database, actor, vehicle, record) == before
    finally:
        native_database._parts[second.id] = reservation


def test_untracked_catalog_replacement_blocks_cleanup_and_preserves_row(native_database, actors, owned):
    vehicle, record = owned
    actor = actors[0]
    application = controller(native_database)
    original = manual.browser_catalog_command(application, "create")
    replacement = manual.browser_catalog_command(application, "replace")
    assert replacement.id != original.id
    before = parent_state(native_database, actor, vehicle, record)
    # This test owns both IDs. Temporarily hide only its replacement identity
    # to exercise unknown-writer refusal, restoring it even on assertion failure.
    reservation = native_database._catalog_parts.pop(replacement.id)
    try:
        with pytest.raises(TestDatabaseSafetyError, match="Unexpected catalog ID"):
            native_database.cleanup()
        assert replacement.id not in native_database._catalog_parts
        with native_database.connect(native_database.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT id, manufacturer, part_number, name, category FROM public.parts WHERE id = %s",
                (replacement.id,),
            ).fetchone()
        assert row == tuple(replacement.model_dump().values())
        assert parent_state(native_database, actor, vehicle, record) == before
    finally:
        native_database._catalog_parts[replacement.id] = reservation
