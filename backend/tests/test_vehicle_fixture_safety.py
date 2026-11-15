from unittest.mock import Mock

import pytest

from app.config import Settings, TEST_DATABASE
from app.vehicle_schemas import VehicleCreate
from database_support import NativeTestDatabase, TestDatabaseSafetyError, VEHICLE_MATCH
from test_session_fixture_safety import connection_with


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture
def settings():
    return Settings("unused", 5432, TEST_DATABASE, "synthetic", "")


@pytest.fixture
def vehicle():
    return VehicleCreate(year=2020, make="Synthetic", model="Exact-reservation", vehicle_type="Test")


def owned_native(settings, *extra_connections):
    lookup = connection_with((TEST_DATABASE,), None)
    user = connection_with((TEST_DATABASE,), (42,))
    connect = Mock(side_effect=[lookup, user, *extra_connections])
    native = NativeTestDatabase(settings, connect)
    email = native.reserve_email()
    native.track_user(42, email)
    return native, connect


def test_vehicle_reservation_and_tracking_reject_unowned_inputs_before_connect(settings, vehicle):
    connect = Mock()
    native = NativeTestDatabase(settings, connect)
    with pytest.raises(TestDatabaseSafetyError, match="owner"):
        native.reserve_vehicle(42, vehicle)
    with pytest.raises(TestDatabaseSafetyError, match="before writing"):
        native.track_vehicle(8, 42, vehicle)
    connect.assert_not_called()


def test_existing_vehicle_collision_is_not_claimed(settings, vehicle):
    reservation = connection_with((TEST_DATABASE,), (8,))
    native, _ = owned_native(settings, reservation)
    with pytest.raises(TestDatabaseSafetyError, match="collision"):
        native.reserve_vehicle(42, vehicle)
    assert not native._vehicle_reservations
    assert not native._vehicles
    assert all(call.args[0].startswith("SELECT") for call in reservation.execute.call_args_list)


def test_tracking_requires_exact_owner_and_reserved_values(settings, vehicle):
    reserve = connection_with((TEST_DATABASE,), None)
    tracked = connection_with((TEST_DATABASE,), None)
    native, _ = owned_native(settings, reserve, tracked)
    native.reserve_vehicle(42, vehicle)
    with pytest.raises(TestDatabaseSafetyError, match="ownership"):
        native.track_vehicle(8, 42, vehicle)
    sql, parameters = tracked.execute.call_args.args
    assert sql == "SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s AND " + VEHICLE_MATCH
    assert parameters[:2] == (8, 42)
    assert not native._vehicles


def test_lost_create_recovery_deletes_exact_ids_before_users_and_verifies_separately(settings, vehicle):
    reserve = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [], [(8,), (9,)], None, None, None)
    reader = connection_with((TEST_DATABASE,), [], [], [])
    native, connect = owned_native(settings, reserve, writer, reader)
    native.reserve_vehicle(42, vehicle)
    native.cleanup()
    calls = [call.args for call in writer.execute.call_args_list]
    assert calls[3] == (
        "SELECT id FROM public.vehicles WHERE user_id = %s AND " + VEHICLE_MATCH,
        (42, 2020, "Synthetic", "Exact-reservation", None, "Test", None, None),
    )
    assert calls[4:6] == [
        ("DELETE FROM public.vehicles WHERE id = %s AND user_id = %s", (8, 42)),
        ("DELETE FROM public.vehicles WHERE id = %s AND user_id = %s", (9, 42)),
    ]
    assert calls[-1][0] == "DELETE FROM public.users WHERE id = %s AND email = %s"
    assert reader is not writer
    assert reader.execute.call_args.args == (
        "SELECT id FROM public.vehicles WHERE id = ANY(%s) OR user_id = ANY(%s)", ([8, 9], [42]),
    )
    for connection in (reserve, writer, reader):
        assert connection.execute.call_args_list[0].args == ("SELECT current_database()",)
        assert sum(call.args == ("SELECT current_database()",) for call in connection.execute.call_args_list) == 1
    assert native.cleanup_verified and native.cleanup_vehicle_count == 2
    native.cleanup()
    assert connect.call_count == 5


def test_remaining_vehicle_stops_cleanup_and_retains_recovery_records(settings, vehicle):
    reserve = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [], [(8,)], None, None)
    reader = connection_with((TEST_DATABASE,), [], [], [(8,)])
    native, _ = owned_native(settings, reserve, writer, reader)
    native.reserve_vehicle(42, vehicle)
    with pytest.raises(pytest.fail.Exception, match="verification failed"):
        native.cleanup()
    assert not native.cleanup_verified
    assert native._vehicle_reservations
    assert native._vehicles == {8: 42}


def test_vehicle_reservation_wrong_physical_database_never_exposes_writer(settings, vehicle):
    unsafe = connection_with(("garageguide_app",))
    native, _ = owned_native(settings, unsafe)
    with pytest.raises(TestDatabaseSafetyError, match="Connected database"):
        native.reserve_vehicle(42, vehicle)
    unsafe.execute.assert_called_once_with("SELECT current_database()")
    unsafe.close.assert_called_once()
    assert not native._vehicle_reservations


def test_update_guard_rejects_unreserved_owner_before_connect(settings):
    connect = Mock()
    native = NativeTestDatabase(settings, connect)
    with pytest.raises(TestDatabaseSafetyError, match="owner"):
        native.require_reserved_vehicle(8, 42)
    connect.assert_not_called()


def test_update_guard_checks_exact_id_owner_without_matching_mutable_values(settings):
    lookup = connection_with((TEST_DATABASE,), (8,))
    native, _ = owned_native(settings, lookup)
    native._vehicles[8] = 42
    native.cleanup_verified = True
    native.require_reserved_vehicle(8, 42)
    assert lookup.execute.call_args_list[0].args == ("SELECT current_database()",)
    assert lookup.execute.call_args.args == (
        "SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s", (8, 42),
    )
    assert len(lookup.execute.call_args_list) == 2
    assert native._vehicles == {8: 42} and not native.cleanup_verified


@pytest.mark.parametrize("tracked_owner", [None, 99])
def test_update_guard_never_adopts_untracked_owned_vehicle(settings, tracked_owner):
    lookup = connection_with((TEST_DATABASE,), (8,))
    native, _ = owned_native(settings, lookup)
    if tracked_owner is not None:
        native._vehicles[8] = tracked_owner
    before = native._vehicles.copy()
    with pytest.raises(TestDatabaseSafetyError, match="Only tracked"):
        native.require_reserved_vehicle(8, 42)
    assert native._vehicles == before


def test_missing_or_foreign_fixture_vehicle_is_left_for_normal_not_found(settings):
    lookup = connection_with((TEST_DATABASE,), None)
    native, _ = owned_native(settings, lookup)
    native.require_reserved_vehicle(8, 42)
    assert not native._vehicles
    assert lookup.execute.call_args.args[1] == (8, 42)


def test_edited_vehicle_cleanup_uses_tracked_identity_when_original_values_no_longer_match(settings, vehicle):
    reserve = connection_with((TEST_DATABASE,), None)
    writer = connection_with((TEST_DATABASE,), (42,), [], [], None, None)
    reader = connection_with((TEST_DATABASE,), [], [], [])
    native, _ = owned_native(settings, reserve, writer, reader)
    native.reserve_vehicle(42, vehicle)
    native._vehicles[8] = 42
    native.cleanup()
    calls = [call.args for call in writer.execute.call_args_list]
    assert calls[-2] == ("DELETE FROM public.vehicles WHERE id = %s AND user_id = %s", (8, 42))
    assert calls[-1][0] == "DELETE FROM public.users WHERE id = %s AND email = %s"
    assert writer is not reader and native.cleanup_verified and native.cleanup_vehicle_count == 1
    assert reader.execute.call_args.args[1] == ([8], [42])
