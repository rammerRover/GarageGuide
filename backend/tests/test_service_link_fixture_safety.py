from datetime import date
from unittest.mock import Mock

import pytest

from app.config import TEST_DATABASE
from database_support import TestDatabaseSafetyError
from test_service_fixture_safety import owned_native, settings
from test_session_fixture_safety import connection_with


pytestmark = pytest.mark.usefixtures("forbid_database")


def linked_native(settings, *connections):
    native, connect = owned_native(settings, *connections)
    native._services[12] = (8, 42)
    return native, connect


@pytest.mark.parametrize("method,args", [
    ("reserve_part_snapshot", (12, 8, 99)), ("reserve_part_snapshot", (13, 8, 42)),
    ("reserve_maintenance_schedule", (9, 42)),
    ("reserve_maintenance_completion", (30, 13, 8, 42)),
])
def test_link_reservations_reject_unowned_or_untracked_parents_before_connect(settings, method, args):
    native, connect = linked_native(settings)
    before = connect.call_count
    with pytest.raises(TestDatabaseSafetyError, match="exact tracked"):
        getattr(native, method)(*args)
    assert connect.call_count == before


def test_all_link_reservations_are_registered_before_writes_and_bind_exact_ownership(settings):
    part = connection_with((TEST_DATABASE,), None)
    schedule = connection_with((TEST_DATABASE,), None)
    completion = connection_with((TEST_DATABASE,), ("synthetic-schedule",), None)
    native, _ = linked_native(settings, part, schedule, completion)
    part_name = native.reserve_part_snapshot(12, 8, 42)
    schedule_name = native.reserve_maintenance_schedule(8, 42)
    completion.execute.side_effect = [Mock(fetchone=Mock(return_value=(TEST_DATABASE,))),
                                      Mock(fetchone=Mock(return_value=(schedule_name,))),
                                      Mock(fetchone=Mock(return_value=None))]
    native.reserve_maintenance_completion(30, 12, 8, 42)
    assert native._part_reservations == {(12, 8, 42, part_name)}
    assert native._schedule_reservations == {(8, 42, schedule_name)}
    assert native._completion_reservations == {(30, 12, 8, 42)}
    assert native._schedules == {30: (8, 42, schedule_name)}
    assert part.execute.call_args.args[1] == (12, 8, 42, part_name)
    assert completion.execute.call_args.args[1] == (30, 12, 8, 42)
    for connection in (part, schedule, completion):
        assert connection.execute.call_args_list[0].args == ("SELECT current_database()",)
        assert all(call.args[0].startswith("SELECT") for call in connection.execute.call_args_list)
    assert not native.cleanup_verified


@pytest.mark.parametrize("kind", ["part", "schedule"])
def test_existing_link_fixture_collision_is_not_claimed(settings, kind):
    collision = connection_with((TEST_DATABASE,), (999,))
    native, _ = linked_native(settings, collision)
    with pytest.raises(TestDatabaseSafetyError, match="collision"):
        if kind == "part":
            native.reserve_part_snapshot(12, 8, 42)
        else:
            native.reserve_maintenance_schedule(8, 42)
    assert not native._part_reservations and not native._schedule_reservations


def test_completion_never_adopts_an_unreserved_or_foreign_schedule(settings):
    native, connect = linked_native(settings)
    before = connect.call_count
    with pytest.raises(TestDatabaseSafetyError, match="reserved before writing"):
        native.reserve_maintenance_completion(30, 12, 8, 42)
    assert connect.call_count == before
    native._schedule_reservations.add((8, 42, "synthetic-schedule"))
    foreign = connection_with((TEST_DATABASE,), None)
    connect.side_effect = [foreign]
    with pytest.raises(TestDatabaseSafetyError, match="ownership"):
        native.reserve_maintenance_completion(30, 12, 8, 42)
    assert not native._completion_reservations and not native._schedules


def test_existing_completion_is_not_claimed(settings):
    connection = connection_with((TEST_DATABASE,), ("synthetic-schedule",), (999,))
    native, _ = linked_native(settings, connection)
    native._schedule_reservations.add((8, 42, "synthetic-schedule"))
    with pytest.raises(TestDatabaseSafetyError, match="collision"):
        native.reserve_maintenance_completion(30, 12, 8, 42)
    assert not native._completion_reservations and not native._completions


def test_wrong_physical_database_is_closed_before_reserving_children(settings):
    unsafe = connection_with(("garageguide_app",))
    native, _ = linked_native(settings, unsafe)
    with pytest.raises(TestDatabaseSafetyError, match="Connected database"):
        native.reserve_part_snapshot(12, 8, 42)
    unsafe.execute.assert_called_once_with("SELECT current_database()")
    unsafe.close.assert_called_once()
    assert not native._part_reservations


def test_missing_or_deferred_child_foreign_keys_stop_before_fixture_writes(settings):
    native, _ = linked_native(settings)
    for rows in ([], [("FOREIGN KEY (service_record_id) REFERENCES service_records(id) ON DELETE CASCADE", True)]):
        connection = connection_with(rows)
        with pytest.raises(pytest.fail.Exception, match="foreign keys"):
            native._check_linked_schema(connection)
        assert all(call.args[0].startswith("SELECT") for call in connection.execute.call_args_list)


def seed_reservations(native):
    native._service_reservations.add((8, 42, date(2020, 1, 1), "repair", "Synthetic service", None, None, None, None))
    native._part_reservations.add((12, 8, 42, "synthetic-part"))
    native._schedule_reservations.add((8, 42, "synthetic-schedule"))
    native._completion_reservations.add((30, 12, 8, 42))


def cleanup_writer():
    return connection_with((TEST_DATABASE,), (42,), [], [(20,)], [(30,)], [(40,)],
                           None, None, (30,), (False,), None, [(12,)], (12,), (False,), None, None, None)


def test_exact_children_are_recovered_and_deleted_before_services_and_parents(settings):
    writer = cleanup_writer()
    reader = connection_with((TEST_DATABASE,), [], [], [], [], [], [])
    native, _ = linked_native(settings, writer, reader)
    seed_reservations(native)
    native.cleanup()
    calls = [call.args for call in writer.execute.call_args_list]
    deletes = [call for call in calls if call[0].startswith("DELETE")]
    assert [call[0].split(" AS ")[0] for call in deletes] == [
        "DELETE FROM public.maintenance_completions", "DELETE FROM public.service_parts",
        "DELETE FROM public.maintenance_schedules", "DELETE FROM public.service_records",
        "DELETE FROM public.vehicles WHERE id = %s AND user_id = %s",
        "DELETE FROM public.users WHERE id = %s AND email = %s",
    ]
    assert deletes[0][1] == (40, 30, 12, 8, 42)
    assert deletes[1][1] == (20, 12, 8, 42, "synthetic-part")
    assert deletes[2][1] == (30, 8, 42, "synthetic-schedule")
    assert writer is not reader
    assert reader.execute.call_args_list[0].args == ("SELECT current_database()",)
    assert native.cleanup_link_counts == (1, 1, 1) and native.cleanup_service_count == 1
    assert native.cleanup_verified
    assert not native._part_reservations and not native._schedules and not native._completions


def test_unknown_schedule_links_cannot_be_silently_cascaded(settings):
    native, _ = linked_native(settings)
    native._schedule_reservations.add((8, 42, "synthetic-schedule"))
    connection = connection_with([(30,)], (30,), (True,))
    with pytest.raises(TestDatabaseSafetyError, match="no cascade permitted"):
        native._delete_linked_fixtures(connection)
    assert not any(call.args[0].startswith("DELETE") for call in connection.execute.call_args_list)
    assert native._schedules == {30: (8, 42, "synthetic-schedule")}


@pytest.mark.parametrize("remaining", ["part", "schedule", "completion"])
def test_any_remaining_exact_child_fails_verification_and_retains_recovery_metadata(settings, remaining):
    writer = cleanup_writer()
    reader = connection_with((TEST_DATABASE,), [], [], [],
                             [(20,)] if remaining == "part" else [],
                             [(30,)] if remaining == "schedule" else [],
                             [(40,)] if remaining == "completion" else [])
    native, _ = linked_native(settings, writer, reader)
    seed_reservations(native)
    with pytest.raises(pytest.fail.Exception, match="verification failed"):
        native.cleanup()
    assert not native.cleanup_verified
    assert native._parts and native._schedules and native._completions
    assert native._part_reservations and native._completion_reservations
