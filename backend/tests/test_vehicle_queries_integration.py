from contextlib import contextmanager
from uuid import uuid4

import psycopg
import pytest

from app import database, session_queries, user_queries, vehicle_queries
from app.schemas import RegistrationResponse
from app.vehicle_schemas import VehicleCreate


pytestmark = pytest.mark.integration


@pytest.fixture
def actors(native_database):
    result = []
    for _ in range(2):
        email = native_database.reserve_email()
        row = user_queries.create_user(
            native_database.settings, email=email, password_hash="synthetic-unused-credential",
        )
        user = RegistrationResponse(id=row[0], email=row[1], created_at=row[2])
        native_database.track_user(user.id, user.email)
        issued = session_queries.create_session(native_database.settings, user=user)
        native_database.track_session(issued.session.session_id, user.id)
        result.append(session_queries.validate_and_extend_session(native_database.settings, issued.token))
    return result


def reserved_vehicle(native, actor, **overrides):
    request = VehicleCreate(**{
        "year": 2020, "make": "Synthetic' -- \u00e9", "model": f"gg-vehicle-{uuid4().hex}",
        "vehicle_type": "Custom \U0001f6f5", **overrides,
    })
    native.reserve_vehicle(actor.user.id, request)
    return request


def create_owned(native, actor, request):
    vehicle = vehicle_queries.create_vehicle(native.settings, actor=actor, vehicle=request)
    native.track_vehicle(vehicle.id, actor.user.id, request)
    return vehicle


@pytest.mark.parametrize(
    ("mileage", "hours"), [(None, None), ("0.0", None), (None, "0.0"), ("99999999999.9", "12.3")],
)
def test_committed_readings_and_database_timestamps(native_database, actors, mileage, hours):
    actor = actors[0]
    request = reserved_vehicle(native_database, actor, mileage=mileage, operating_hours=hours)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        before = connection.execute("SELECT clock_timestamp()").fetchone()[0]
    vehicle = create_owned(native_database, actor, request)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        row = connection.execute(
            "SELECT user_id, mileage, operating_hours, readings_updated_at, created_at, clock_timestamp() "
            "FROM public.vehicles WHERE id = %s AND user_id = %s", (vehicle.id, actor.user.id),
        ).fetchone()
    assert row[0] == actor.user.id
    assert row[1:3] == (request.mileage, request.operating_hours)
    assert before <= row[4] <= row[5]
    if mileage is None and hours is None:
        assert row[3] is None
    else:
        assert row[3] == row[4]
    public = vehicle.model_dump(mode="json")
    assert public["mileage"] == mileage
    assert public["operating_hours"] == hours
    assert "user_id" not in public


def test_owned_lists_are_isolated_and_empty_for_other_user(native_database, actors):
    first, second = actors
    assert vehicle_queries.list_vehicles(native_database.settings, actor=first).vehicles == []
    one = create_owned(native_database, first, reserved_vehicle(native_database, first))
    assert vehicle_queries.list_vehicles(native_database.settings, actor=second).vehicles == []
    two = create_owned(native_database, second, reserved_vehicle(native_database, second))
    assert vehicle_queries.list_vehicles(native_database.settings, actor=first).vehicles == [one]
    assert vehicle_queries.list_vehicles(native_database.settings, actor=second).vehicles == [two]


def test_identical_vehicles_are_distinct_and_tie_order_uses_descending_id(native_database, actors):
    actor = actors[0]
    request = reserved_vehicle(native_database, actor)
    first = create_owned(native_database, actor, request)
    second = create_owned(native_database, actor, request)
    assert first.id != second.id
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "UPDATE public.vehicles SET created_at = %s WHERE id = ANY(%s) AND user_id = %s",
            (first.created_at, [first.id, second.id], actor.user.id),
        )
    listed = vehicle_queries.list_vehicles(native_database.settings, actor=actor).vehicles
    assert [item.id for item in listed] == [second.id, first.id]


def test_lost_response_recovers_exact_vehicle_and_cleanup_is_verified(native_database, actors):
    actor = actors[0]
    request = reserved_vehicle(native_database, actor)
    with pytest.raises(RuntimeError, match="Synthetic lost response"):
        vehicle_queries.create_vehicle(native_database.settings, actor=actor, vehicle=request)
        raise RuntimeError("Synthetic lost response")
    native_database.cleanup()
    assert native_database.cleanup_verified
    assert native_database.cleanup_vehicle_count == 1
    assert native_database.cleanup_counts == (2, 2)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        assert connection.execute(
            "SELECT id FROM public.vehicles WHERE user_id = ANY(%s)",
            ([actor.user.id for actor in actors],),
        ).fetchall() == []


def test_preparation_failure_rolls_back_before_cleanup(native_database, actors, monkeypatch):
    actor = actors[0]
    request = reserved_vehicle(native_database, actor)
    original = vehicle_queries._public_vehicle
    def fail_preparation(row):
        raise RuntimeError("Synthetic preparation failure")

    monkeypatch.setattr(vehicle_queries, "_public_vehicle", fail_preparation)
    with pytest.raises(RuntimeError, match="Synthetic preparation failure"):
        vehicle_queries.create_vehicle(native_database.settings, actor=actor, vehicle=request)
    monkeypatch.setattr(vehicle_queries, "_public_vehicle", original)
    assert vehicle_queries.list_vehicles(native_database.settings, actor=actor).vehicles == []


def test_lost_commit_acknowledgment_recovers_committed_vehicle(native_database, actors, monkeypatch):
    actor = actors[0]
    request = reserved_vehicle(native_database, actor)
    connections = []

    @contextmanager
    def lose_acknowledgment(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            connections.append(connection)
            yield connection
        raise psycopg.OperationalError("Synthetic lost acknowledgment after real commit")

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", lose_acknowledgment)
        with pytest.raises(vehicle_queries.VehicleUnavailableError):
            vehicle_queries.create_vehicle(native_database.settings, actor=actor, vehicle=request)
    assert connections[0].closed
    assert len(vehicle_queries.list_vehicles(native_database.settings, actor=actor).vehicles) == 1
    native_database.cleanup()
    assert native_database.cleanup_verified and native_database.cleanup_vehicle_count == 1
