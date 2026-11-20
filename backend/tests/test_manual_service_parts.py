from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app import service_part_queries
from app.service_part_schemas import CatalogPartPreview, CatalogServicePartCreate, ManualServicePartCreate, ServicePartRemovalRequest
from database_support import TestDatabaseSafetyError
from test_manual_registration_server import guarded_setup
from test_session_fixture_safety import connection_with
import manual_registration_server as manual


pytestmark = pytest.mark.usefixtures("forbid_database")
PREVIEW = CatalogPartPreview(id=22, manufacturer="synthetic-maker", part_number="synthetic-number", name="synthetic-part", category="Synthetic")


@pytest.mark.parametrize("operation", ["list_service_parts", "lookup_catalog_part", "attach_service_part", "remove_service_part"])
def test_guarded_browser_part_routes_reject_unreserved_parents_before_query(guarded_setup, monkeypatch, operation):
    settings, native, _, _ = guarded_setup
    original = Mock()
    monkeypatch.setattr(service_part_queries, operation, original)
    native.require_reserved_parts.side_effect = TestDatabaseSafetyError("Unreserved service")
    with manual.prepared_test_backend():
        with pytest.raises(TestDatabaseSafetyError):
            getattr(service_part_queries, operation)(settings, actor=Mock(user=Mock(id=7, email="reserved-0@example.com")),
                vehicle_id=8, service_id=12, **({"lookup": PREVIEW} if operation == "lookup_catalog_part" else
                    {"part": ManualServicePartCreate(source="manual", name="Synthetic")} if operation == "attach_service_part" else
                    {"snapshot_id": 20, "confirmation": ServicePartRemovalRequest(confirm_removal=True)} if operation == "remove_service_part" else {}))
        original.assert_not_called()
    assert getattr(service_part_queries, operation) is original


def test_browser_attachment_reserves_before_write_and_tracks_exact_result(guarded_setup, monkeypatch):
    settings, native, _, _ = guarded_setup
    events = []
    native.require_reserved_parts.return_value = True
    native.reserve_part_snapshot.side_effect = lambda *a, **k: events.append("reserve")
    native.remember_part_snapshot.side_effect = lambda *a, **k: events.append("capture")
    native.track_part_snapshot.side_effect = lambda *a, **k: events.append("track")
    def insert(*a, **kwargs):
        result = SimpleNamespace(id=20, name="Synthetic")
        events.append("insert")
        kwargs["prepare_response"](result)
        events.append("commit")
        return result
    original = Mock(side_effect=insert)
    monkeypatch.setattr(service_part_queries, "attach_service_part", original)
    actor = Mock(user=Mock(id=7, email="reserved-0@example.com"))
    with manual.prepared_test_backend():
        service_part_queries.attach_service_part(settings, actor=actor, vehicle_id=8, service_id=12,
            part=ManualServicePartCreate(source="manual", name="Synthetic"))
    assert events == ["reserve", "insert", "capture", "commit", "track"]
    native.reserve_part_snapshot.assert_called_once_with(12, 8, 7, name="Synthetic")
    native.track_part_snapshot.assert_called_once_with(20, 12, 8, 7, "Synthetic")


@pytest.mark.parametrize("failure", ["lost-ack", "response-preparation"])
def test_browser_attachment_captures_id_before_preparation_or_lost_ack_failure(guarded_setup, monkeypatch, failure):
    settings, native, _, _ = guarded_setup
    native.require_reserved_parts.return_value = True
    result = SimpleNamespace(id=20, name="Synthetic")
    events = []
    native.remember_part_snapshot.side_effect = lambda *a: events.append("capture")
    def insert(*args, **kwargs):
        kwargs["prepare_response"](result)
        events.append("commit")
        raise RuntimeError("Synthetic lost acknowledgment")
    def prepare(value):
        assert value is result
        events.append("prepare")
        if failure == "response-preparation":
            raise RuntimeError("Synthetic response preparation failure")
    monkeypatch.setattr(service_part_queries, "attach_service_part", insert)
    with manual.prepared_test_backend():
        with pytest.raises(RuntimeError):
            service_part_queries.attach_service_part(settings, actor=Mock(user=Mock(id=7, email="reserved-0@example.com")),
                vehicle_id=8, service_id=12, part=ManualServicePartCreate(source="manual", name="Synthetic"), prepare_response=prepare)
    assert events == (["capture", "prepare", "commit"] if failure == "lost-ack" else ["capture", "prepare"])
    native.remember_part_snapshot.assert_called_once_with(20, 12, 8, 7, "Synthetic")
    native.track_part_snapshot.assert_not_called()


def test_browser_catalog_attachment_never_uses_ordinary_catalog_rows(guarded_setup, monkeypatch):
    settings, native, _, _ = guarded_setup
    original = Mock()
    monkeypatch.setattr(service_part_queries, "attach_service_part", original)
    native.require_reserved_parts.return_value = True
    native.require_reserved_catalog_pair.side_effect = TestDatabaseSafetyError("Ordinary catalog entry")
    with manual.prepared_test_backend():
        with pytest.raises(TestDatabaseSafetyError):
            service_part_queries.attach_service_part(settings, actor=Mock(user=Mock(id=7, email="reserved-0@example.com")),
                vehicle_id=8, service_id=12, part=CatalogServicePartCreate(source="catalog", preview=PREVIEW))
    original.assert_not_called()
    native.reserve_part_snapshot.assert_not_called()


def test_browser_empty_catalog_preflight_never_deletes_existing_rows(guarded_setup):
    _, native, _, _ = guarded_setup
    connection = connection_with((True,))
    native.connect.return_value = connection
    with pytest.raises(TestDatabaseSafetyError, match="empty test catalog"):
        with manual.prepared_test_backend(service_parts=True):
            pytest.fail("Nonempty catalog was exposed as empty")
    connection.execute.assert_called_once_with("SELECT EXISTS (SELECT 1 FROM public.parts)")
    native.cleanup.assert_called_once()


def context_for(connection, *, preview=PREVIEW, snapshots=None):
    native = Mock()
    native._catalog_parts = {PREVIEW.id: (PREVIEW.manufacturer, PREVIEW.part_number)}
    native._parts = snapshots or {}
    native.connect.return_value = connection
    application = SimpleNamespace(state=SimpleNamespace(browser_catalog={"native": native, "settings": Mock(), "preview": preview}))
    return application, native


def test_catalog_create_is_reserved_before_insertion_and_tracked_afterwards():
    fields = PREVIEW.model_dump(exclude={"id"})
    connection = connection_with(tuple(PREVIEW.model_dump().values()))
    application, native = context_for(connection, preview=None)
    native.reserve_catalog_part.return_value = fields
    result = manual.browser_catalog_command(application, "create")
    assert result == PREVIEW
    assert [call[0] for call in native.method_calls] == ["reserve_catalog_part", "connect", "track_catalog_part"]
    native.track_catalog_part.assert_called_once_with(22, PREVIEW.manufacturer, PREVIEW.part_number)
    assert connection.execute.call_args.args[1] == tuple(fields.values())


def test_catalog_change_targets_only_the_owned_id():
    changed = {**PREVIEW.model_dump(), "name": PREVIEW.name + " revised"}
    connection = connection_with((22,), tuple(changed.values()))
    application, _ = context_for(connection)
    assert manual.browser_catalog_command(application, "change").model_dump() == changed
    sql, parameters = connection.execute.call_args.args
    assert sql.startswith("UPDATE public.parts SET name = %s WHERE id = %s")
    assert parameters == (changed["name"], 22)


@pytest.mark.parametrize("unknown", ["snapshot", "saved-or-fitment"])
def test_catalog_deletion_rejects_untracked_linked_data(unknown):
    connection = connection_with((22,), [(99, 12, 8, 7, "untracked")] if unknown == "snapshot" else [], (True,))
    application, _ = context_for(connection)
    with pytest.raises(TestDatabaseSafetyError, match="reference"):
        manual.browser_catalog_command(application, "delete")
    assert not any(call.args[0].startswith("DELETE") for call in connection.execute.call_args_list)
    assert application.state.browser_catalog["preview"] == PREVIEW


def test_catalog_deletion_permits_only_exact_known_snapshot_references():
    connection = connection_with((22,), [(90, 12, 8, 7, "synthetic-copy")], (False,), None)
    application, _ = context_for(connection, snapshots={90: (12, 8, 7, "synthetic-copy")})
    assert manual.browser_catalog_command(application, "delete") is None
    deletes = [call.args for call in connection.execute.call_args_list if call.args[0].startswith("DELETE")]
    assert deletes == [("DELETE FROM public.parts WHERE id = %s", (22,))]


@pytest.mark.parametrize("command", ["change", "delete", "replace", "unrecognized"])
def test_catalog_commands_cannot_target_an_untracked_entry(command):
    application, native = context_for(Mock())
    native._catalog_parts.clear()
    with pytest.raises(TestDatabaseSafetyError):
        manual.browser_catalog_command(application, command)
    native.connect.assert_not_called()


def test_prepared_backend_never_cleans_up_while_browser_server_is_still_running(guarded_setup):
    _, native, _, _ = guarded_setup
    native.browser_server_running = False
    with pytest.raises(TestDatabaseSafetyError, match="still active"):
        with manual.prepared_test_backend():
            native.browser_server_running = True
    native.cleanup.assert_not_called()


def test_browser_parts_launcher_preserves_default_and_reports_extended_cleanup(guarded_setup, monkeypatch, capsys):
    _, native, _, _ = guarded_setup
    native.connect.return_value = connection_with((False,))
    run = Mock()
    monkeypatch.setattr(manual, "run_browser_parts_terminal", run)
    assert manual.main(["--service-parts"]) == 0
    run.assert_called_once()
    assert "catalog entries are absent" in capsys.readouterr().out
