from unittest.mock import Mock

import pytest

from app.config import TEST_DATABASE
from database_support import NativeTestDatabase, TestDatabaseSafetyError
from test_service_link_fixture_safety import linked_native
from test_session_fixture_safety import connection_with, settings


pytestmark = pytest.mark.usefixtures("forbid_database")


def test_catalog_reservation_is_exact_synthetic_and_read_only(settings):
    connection = connection_with((TEST_DATABASE,), None)
    native = NativeTestDatabase(settings, Mock(return_value=connection))
    fields = native.reserve_catalog_part()
    assert fields["manufacturer"].startswith("gg-catalog-maker-")
    assert fields["part_number"].startswith("gg-catalog-number-")
    assert fields["name"].startswith("gg-catalog-part-")
    pair = (fields["manufacturer"], fields["part_number"])
    assert native._catalog_reservations == {pair}
    assert connection.execute.call_args.args[1] == pair
    assert connection.execute.call_args_list[0].args == ("SELECT current_database()",)
    assert all(call.args[0].startswith("SELECT") for call in connection.execute.call_args_list)


def test_catalog_collision_cannot_be_claimed(settings):
    native = NativeTestDatabase(settings, Mock(return_value=connection_with((TEST_DATABASE,), (99,))))
    with pytest.raises(TestDatabaseSafetyError, match="collision"):
        native.reserve_catalog_part()
    assert not native._catalog_reservations and not native._catalog_parts


def test_catalog_tracking_requires_reservation_and_exact_verified_row(settings):
    connector = Mock()
    native = NativeTestDatabase(settings, connector)
    with pytest.raises(TestDatabaseSafetyError, match="reserved before"):
        native.track_catalog_part(22, "ordinary", "ordinary")
    connector.assert_not_called()
    native._catalog_reservations.add(("synthetic-maker", "synthetic-number"))
    connector.return_value = connection_with((TEST_DATABASE,), None)
    with pytest.raises(TestDatabaseSafetyError, match="identity"):
        native.track_catalog_part(22, "synthetic-maker", "synthetic-number")
    assert not native._catalog_parts


def test_snapshot_reservation_and_tracking_require_exact_owner_and_parent(settings):
    reserve = connection_with((TEST_DATABASE,), None)
    track = connection_with((TEST_DATABASE,), (22,))
    native, connect = linked_native(settings, reserve, track)
    assert native.reserve_part_snapshot(12, 8, 42, name="synthetic-catalog-copy") == "synthetic-catalog-copy"
    native.track_part_snapshot(22, 12, 8, 42, "synthetic-catalog-copy")
    assert native._parts == {22: (12, 8, 42, "synthetic-catalog-copy")}
    assert track.execute.call_args.args[1] == (22, 12, 8, 42, "synthetic-catalog-copy")
    before = connect.call_count
    with pytest.raises(TestDatabaseSafetyError):
        native.track_part_snapshot(23, 12, 8, 99, "synthetic-catalog-copy")
    with pytest.raises(TestDatabaseSafetyError, match="reserved before"):
        native.track_part_snapshot(23, 12, 8, 42, "unreserved")
    assert connect.call_count == before


def test_catalog_snapshot_collision_is_not_adopted(settings):
    native, _ = linked_native(settings, connection_with((TEST_DATABASE,), (99,)))
    with pytest.raises(TestDatabaseSafetyError, match="collision"):
        native.reserve_part_snapshot(12, 8, 42, name="existing-name")
    assert not native._part_reservations


@pytest.mark.parametrize("connected", ["garageguide_app", "postgres", "other"])
def test_catalog_guard_rejects_wrong_physical_database_before_any_fixture_query(settings, connected):
    connection = connection_with((connected,))
    native = NativeTestDatabase(settings, Mock(return_value=connection))
    with pytest.raises(TestDatabaseSafetyError, match="Connected database"):
        native.reserve_catalog_part()
    connection.execute.assert_called_once_with("SELECT current_database()")
    connection.close.assert_called_once()
    assert not native._catalog_reservations


@pytest.mark.parametrize("tracked", [False, True])
def test_catalog_only_cleanup_recovers_lost_ack_and_uses_separate_guarded_verification(settings, tracked):
    writer = connection_with((TEST_DATABASE,), [(22,)], (22,), (False,), None)
    reader = connection_with((TEST_DATABASE,), [], [], [], [])
    native = NativeTestDatabase(settings, Mock(side_effect=[writer, reader]))
    native._catalog_reservations.add(("synthetic-maker", "synthetic-number"))
    if tracked:
        native._catalog_parts[22] = ("synthetic-maker", "synthetic-number")
    native.cleanup()
    deletes = [call.args for call in writer.execute.call_args_list if call.args[0].startswith("DELETE")]
    assert deletes == [("DELETE FROM public.parts WHERE id = %s", (22,))]
    assert writer is not reader
    for connection in [writer, reader]:
        assert connection.execute.call_args_list[0].args == ("SELECT current_database()",)
    assert native.cleanup_catalog_count == 1 and native.cleanup_verified
    assert not native._catalog_reservations and not native._catalog_parts


def test_catalog_cleanup_uses_tracked_id_after_identity_edits(settings):
    native = NativeTestDatabase(settings, Mock())
    native._catalog_reservations.add(("old-maker", "old-number"))
    native._catalog_parts[22] = ("old-maker", "old-number")
    connection = connection_with([], (22,), (False,), None)
    native._delete_catalog_fixtures(connection)
    assert connection.execute.call_args.args == ("DELETE FROM public.parts WHERE id = %s", (22,))
    assert connection.execute.call_args_list[1].args == ("SELECT id FROM public.parts WHERE id = %s FOR UPDATE", (22,))


def test_catalog_cleanup_refuses_unexpected_references_instead_of_set_null(settings):
    native = NativeTestDatabase(settings, Mock())
    native._catalog_parts[22] = ("synthetic-maker", "synthetic-number")
    connection = connection_with((22,), (True,))
    with pytest.raises(TestDatabaseSafetyError, match="no SET NULL"):
        native._delete_catalog_fixtures(connection)
    assert not any(call.args[0].startswith("DELETE") for call in connection.execute.call_args_list)
    assert connection.execute.call_args.args[1] == (22, 22, 22)


def test_remaining_catalog_rows_prevent_claiming_cleanup_success(settings):
    writer = connection_with((TEST_DATABASE,), [(22,)], (22,), (False,), None)
    reader = connection_with((TEST_DATABASE,), [], [], [(22,)], [])
    native = NativeTestDatabase(settings, Mock(side_effect=[writer, reader]))
    native._catalog_reservations.add(("synthetic-maker", "synthetic-number"))
    with pytest.raises(pytest.fail.Exception, match="verification failed"):
        native.cleanup()
    assert not native.cleanup_verified and native._catalog_parts == {22: ("synthetic-maker", "synthetic-number")}


def test_catalog_schema_guard_is_read_only_and_rejects_missing_constraints(settings):
    native = NativeTestDatabase(settings, Mock())
    connection = connection_with(None, None, [], [])
    with pytest.raises(pytest.fail.Exception, match="constraints"):
        native._check_catalog_schema(connection)
    assert all(call.args[0].startswith("SELECT") for call in connection.execute.call_args_list)


@pytest.mark.parametrize("known", [False, True])
def test_browser_catalog_guard_rejects_an_existing_untracked_catalog_id(settings, known):
    connection = connection_with((TEST_DATABASE,), (22,))
    native = NativeTestDatabase(settings, Mock(return_value=connection))
    if known:
        native._catalog_parts[22] = ("synthetic", "number")
        assert native.require_reserved_catalog_pair("synthetic", "number")
    else:
        with pytest.raises(TestDatabaseSafetyError, match="synthetic catalog"):
            native.require_reserved_catalog_pair("ordinary", "number")
    assert connection.execute.call_args_list[0].args == ("SELECT current_database()",)


@pytest.mark.parametrize("known", [False, True])
def test_browser_snapshot_guard_requires_known_id_or_exact_prewrite_reservation(settings, known):
    connection = connection_with((TEST_DATABASE,), [(22, "synthetic")])
    native = NativeTestDatabase(settings, Mock(return_value=connection))
    native.require_reserved_service = Mock(return_value=True)
    if known:
        native._part_reservations.add((12, 8, 42, "synthetic"))
        assert native.require_reserved_parts(12, 8, 42)
        assert native._parts[22] == (12, 8, 42, "synthetic")
    else:
        with pytest.raises(TestDatabaseSafetyError, match="synthetic part"):
            native.require_reserved_parts(12, 8, 42)
        assert not native._parts
    assert connection.execute.call_args_list[0].args == ("SELECT current_database()",)
