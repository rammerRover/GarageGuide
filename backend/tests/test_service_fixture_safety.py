from datetime import date
from unittest.mock import Mock

import pytest

from app.config import Settings, TEST_DATABASE
from app.service_schemas import ServiceCreate
from database_support import NativeTestDatabase, SERVICE_MATCH, TestDatabaseSafetyError
from test_session_fixture_safety import connection_with


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture
def settings():
    return Settings("unused", 5432, TEST_DATABASE, "synthetic", "")


@pytest.fixture
def service():
    return ServiceCreate(service_date="2020-01-01", service_type="repair", description="Unique synthetic service")


def owned_native(settings, *connections):
    lookup = connection_with((TEST_DATABASE,), None)
    user = connection_with((TEST_DATABASE,), (42,))
    connect = Mock(side_effect=[lookup, user, *connections])
    native = NativeTestDatabase(settings, connect)
    email = native.reserve_email()
    native.track_user(42, email)
    native._vehicles[8] = 42
    return native, connect


@pytest.mark.parametrize("owner,vehicle", [(99, 8), (42, 9)])
def test_service_reservation_requires_exact_fixture_parent_before_connect(settings, service, owner, vehicle):
    native, connect = owned_native(settings)
    before = connect.call_count
    with pytest.raises(TestDatabaseSafetyError, match="exact tracked"):
        native.reserve_service(vehicle, owner, service)
    assert connect.call_count == before and not native._service_reservations


def test_tracking_unreserved_service_does_not_connect(settings, service):
    connect = Mock()
    native = NativeTestDatabase(settings, connect)
    with pytest.raises(TestDatabaseSafetyError, match="before writing"):
        native.track_service(12, 8, 42, service)
    connect.assert_not_called()


def test_reservation_does_not_claim_existing_service(settings, service):
    reserve = connection_with((TEST_DATABASE,), (12,))
    native, _ = owned_native(settings, reserve)
    with pytest.raises(TestDatabaseSafetyError, match="collision"):
        native.reserve_service(8, 42, service)
    assert not native._service_reservations and not native._services
    assert reserve.execute.call_args.args[1] == (8, 42, date(2020, 1, 1), "repair", service.description, None, None, None, None)


@pytest.mark.parametrize("result", [None, (999,)])
def test_tracking_checks_id_owner_parent_and_reserved_values(settings, service, result):
    reserve = connection_with((TEST_DATABASE,), None)
    tracked = connection_with((TEST_DATABASE,), result)
    native, _ = owned_native(settings, reserve, tracked)
    native.reserve_service(8, 42, service)
    with pytest.raises(TestDatabaseSafetyError, match="ownership"):
        native.track_service(12, 8, 42, service)
    sql, parameters = tracked.execute.call_args.args
    assert sql.endswith("WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s AND " + SERVICE_MATCH)
    assert parameters[:3] == (12, 8, 42)
    assert not native._services


def test_successful_tracking_retains_immutable_identity(settings, service):
    reserve = connection_with((TEST_DATABASE,), None)
    tracked = connection_with((TEST_DATABASE,), (12,))
    native, _ = owned_native(settings, reserve, tracked)
    native.reserve_service(8, 42, service)
    native.track_service(12, 8, 42, service)
    assert native._services == {12: (8, 42)}
    assert not native.cleanup_verified


@pytest.mark.parametrize("row,tracked,allowed", [(None, False, True), ((12,), True, True), ((12,), False, False)])
def test_manual_service_identity_checks_parent_owner_and_immutable_tracking(settings, row, tracked, allowed):
    parent = connection_with((TEST_DATABASE,), (8,))
    record = connection_with((TEST_DATABASE,), row)
    native, connect = owned_native(settings, parent, record)
    if tracked:
        native._services[12] = (8, 42)
    if allowed:
        assert native.require_reserved_service(12, 8, 42) is (row is not None)
    else:
        with pytest.raises(TestDatabaseSafetyError, match="Only tracked synthetic service"):
            native.require_reserved_service(12, 8, 42)
    sql, params = record.execute.call_args.args
    assert "s.id = %s AND s.vehicle_id = %s AND v.user_id = %s" in sql
    assert params == (12, 8, 42)
    assert parent.execute.call_args_list[0].args == ("SELECT current_database()",)
    assert record.execute.call_args_list[0].args == ("SELECT current_database()",)
    assert connect.call_count == 4


def test_wrong_physical_database_is_closed_before_reservation_or_write(settings, service):
    unsafe = connection_with(("garageguide_app",))
    native, _ = owned_native(settings, unsafe)
    with pytest.raises(TestDatabaseSafetyError, match="Connected database"):
        native.reserve_service(8, 42, service)
    unsafe.execute.assert_called_once_with("SELECT current_database()")
    unsafe.close.assert_called_once()
    assert not native._service_reservations


def test_lost_ack_recovery_deletes_exact_services_before_vehicles_and_verifies_separately(settings, service):
    reserve = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [], [(12,), (13,)],
                             (12,), (False,), None, (13,), (False,), None, None, None)
    reader = connection_with((TEST_DATABASE,), [], [], [])
    native, connect = owned_native(settings, reserve, writer, reader)
    native.reserve_service(8, 42, service)
    native.cleanup()
    calls = [call.args for call in writer.execute.call_args_list]
    service_deletes = [args for args in calls if args[0].startswith("DELETE FROM public.service_records")]
    assert [args[1] for args in service_deletes] == [(12, 8, 42), (13, 8, 42)]
    vehicle_delete = next(args for args in calls if args[0].startswith("DELETE FROM public.vehicles"))
    assert calls.index(service_deletes[-1]) < calls.index(vehicle_delete)
    assert "FOR UPDATE OF s" in calls[4][0]
    assert reader is not writer
    assert reader.execute.call_args.args[1] == ([12, 13], [8], [42])
    for connection in (reserve, writer, reader):
        assert connection.execute.call_args_list[0].args == ("SELECT current_database()",)
        assert sum(call.args == ("SELECT current_database()",) for call in connection.execute.call_args_list) == 1
    assert native.cleanup_verified and native.cleanup_service_count == 2
    assert native.cleanup_vehicle_count == 1 and native.cleanup_counts == (1, 0)
    assert not native._services and not native._service_reservations
    native.cleanup()
    assert connect.call_count == 5


def test_remaining_service_fails_cleanup_and_retains_recovery_records(settings, service):
    reserve = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [], [(12,)], (12,), (False,), None, None, None)
    reader = connection_with((TEST_DATABASE,), [], [], [(12,)])
    native, _ = owned_native(settings, reserve, writer, reader)
    native.reserve_service(8, 42, service)
    with pytest.raises(pytest.fail.Exception, match="verification failed"):
        native.cleanup()
    assert not native.cleanup_verified and native._service_reservations
    assert native._services == {12: (8, 42)}


@pytest.mark.parametrize("linked", [(True,), None])
def test_cleanup_locks_then_refuses_unknown_or_linked_children_without_deleting(settings, service, linked):
    reserve = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [], [(12,)], (12,), linked)
    native, _ = owned_native(settings, reserve, writer)
    native.reserve_service(8, 42, service)
    with pytest.raises(TestDatabaseSafetyError, match="no cascade permitted"):
        native.cleanup()
    sql = [call.args[0] for call in writer.execute.call_args_list]
    assert not any(statement.startswith("DELETE") for statement in sql)
    assert "FOR UPDATE OF s" in sql[-2]
    assert not native.cleanup_verified and native._services == {12: (8, 42)}


def test_cleanup_uses_tracked_identity_after_mutable_values_change(settings, service):
    reserve = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [], [], (12,), (False,), None, None, None)
    reader = connection_with((TEST_DATABASE,), [], [], [])
    native, _ = owned_native(settings, reserve, writer, reader)
    native.reserve_service(8, 42, service)
    native._services[12] = (8, 42)
    native.cleanup()
    delete = next(call.args for call in writer.execute.call_args_list if call.args[0].startswith("DELETE FROM public.service_records"))
    assert delete[1] == (12, 8, 42)
    assert service.description not in delete[0]
    assert native.cleanup_verified and native.cleanup_service_count == 1
