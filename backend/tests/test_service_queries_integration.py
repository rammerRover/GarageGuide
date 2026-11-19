from contextlib import contextmanager
from datetime import date, timedelta
from itertools import product
from uuid import uuid4

import psycopg
import pytest

from app import database, service_queries, vehicle_queries
from app.service_schemas import ServiceCreate
from app.vehicle_queries import VehicleNotFoundError
from test_vehicle_queries_integration import actors, create_owned, reserved_vehicle


pytestmark = pytest.mark.integration


def owned_vehicle(native, actor):
    return create_owned(native, actor, reserved_vehicle(native, actor, mileage="1000.0", operating_hours="10.0"))


def reserved_service(native, actor, vehicle, **overrides):
    request = ServiceCreate(**{
        "service_date": "2020-02-29", "service_type": "maintenance",
        "description": f"gg-service-{uuid4().hex} Quote' -- \u00e9 \U0001f6f5", **overrides,
    })
    native.reserve_service(vehicle.id, actor.user.id, request)
    return request


def create_owned_service(native, actor, vehicle, request):
    result = service_queries.create_service(native.settings, actor=actor, vehicle_id=vehicle.id, service=request)
    native.track_service(result.id, vehicle.id, actor.user.id, request)
    return result


@pytest.mark.parametrize("mileage,hours,cost", list(product([None, "0.0"], [None, "0.0"], [None, "0.00"])))
def test_committed_service_preserves_exact_unknown_and_zero_values_without_changing_vehicle(native_database, actors, mileage, hours, cost):
    actor = actors[0]
    vehicle = owned_vehicle(native_database, actor)
    before = vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id)
    request = reserved_service(native_database, actor, vehicle, mileage=mileage, operating_hours=hours, cost=cost)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        before_insert = connection.execute("SELECT clock_timestamp()").fetchone()[0]
    result = create_owned_service(native_database, actor, vehicle, request)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        row = connection.execute(
            "SELECT s.service_date, s.mileage, s.operating_hours, s.cost, s.created_at, clock_timestamp() "
            "FROM public.service_records AS s JOIN public.vehicles AS v ON v.id = s.vehicle_id "
            "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
            (result.id, vehicle.id, actor.user.id),
        ).fetchone()
    assert row[:4] == (date(2020, 2, 29), request.mileage, request.operating_hours, request.cost)
    assert before_insert <= row[4] <= row[5]
    output = result.model_dump(mode="json")
    assert (output["mileage"], output["operating_hours"], output["cost"]) == (mileage, hours, cost)
    assert set(output) == set(service_queries.PUBLIC_FIELDS)
    assert vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id) == before


def test_maximum_decimals_and_text_round_trip_exactly(native_database, actors):
    actor = actors[0]
    vehicle = owned_vehicle(native_database, actor)
    request = reserved_service(native_database, actor, vehicle, mileage="99999999999.9", operating_hours="99999999999.9",
                               cost="9999999999.99", notes="  Exact \u00e9 notes\nSecond line  ")
    created = create_owned_service(native_database, actor, vehicle, request)
    listed = service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id)
    assert listed.services == [created]
    assert created.mileage == request.mileage and created.operating_hours == request.operating_hours
    assert created.cost == request.cost and created.notes == "Exact \u00e9 notes\nSecond line"


def test_owned_empty_history_and_two_account_and_two_vehicle_isolation(native_database, actors):
    first, second = actors
    first_vehicle, second_vehicle = owned_vehicle(native_database, first), owned_vehicle(native_database, second)
    other_vehicle = owned_vehicle(native_database, first)
    assert service_queries.list_services(native_database.settings, actor=first, vehicle_id=first_vehicle.id).services == []
    one = create_owned_service(native_database, first, first_vehicle, reserved_service(native_database, first, first_vehicle))
    two = create_owned_service(native_database, second, second_vehicle, reserved_service(native_database, second, second_vehicle))
    assert service_queries.list_services(native_database.settings, actor=first, vehicle_id=first_vehicle.id).services == [one]
    assert service_queries.list_services(native_database.settings, actor=second, vehicle_id=second_vehicle.id).services == [two]
    assert service_queries.list_services(native_database.settings, actor=first, vehicle_id=other_vehicle.id).services == []


@pytest.mark.parametrize("operation", ["list", "create"])
def test_missing_and_foreign_parents_have_the_same_not_found_outcome(native_database, actors, operation):
    first, second = actors
    foreign_vehicle = owned_vehicle(native_database, second)
    own_vehicle = owned_vehicle(native_database, first)
    missing_vehicle = owned_vehicle(native_database, first)
    request = reserved_service(native_database, first, own_vehicle)
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "DELETE FROM public.vehicles WHERE id = %s AND user_id = %s",
            (missing_vehicle.id, first.user.id),
        )
    outcomes = []
    for vehicle_id in (missing_vehicle.id, foreign_vehicle.id):
        with pytest.raises(VehicleNotFoundError) as caught:
            if operation == "list":
                service_queries.list_services(native_database.settings, actor=first, vehicle_id=vehicle_id)
            else:
                service_queries.create_service(native_database.settings, actor=first, vehicle_id=vehicle_id, service=request)
        outcomes.append(str(caught.value))
    assert outcomes == ["Vehicle not found.", "Vehicle not found."]
    assert service_queries.list_services(native_database.settings, actor=second, vehicle_id=foreign_vehicle.id).services == []
    assert service_queries.list_services(native_database.settings, actor=first, vehicle_id=own_vehicle.id).services == []


def test_newest_first_order_uses_date_then_created_at_then_id(native_database, actors):
    actor = actors[0]
    vehicle = owned_vehicle(native_database, actor)
    old = create_owned_service(native_database, actor, vehicle, reserved_service(native_database, actor, vehicle, service_date="2019-01-01"))
    request = reserved_service(native_database, actor, vehicle, service_date="2020-01-01")
    first = create_owned_service(native_database, actor, vehicle, request)
    second = create_owned_service(native_database, actor, vehicle, request)
    latest_date = create_owned_service(native_database, actor, vehicle, reserved_service(native_database, actor, vehicle, service_date="2021-01-01"))
    assert first.id != second.id
    initial = service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id)
    assert [record.id for record in initial.services] == [latest_date.id, second.id, first.id, old.id]
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "UPDATE public.service_records AS s SET created_at = %s FROM public.vehicles AS v "
            "WHERE s.id = %s AND s.vehicle_id = %s AND v.id = s.vehicle_id AND v.user_id = %s",
            (second.created_at + timedelta(seconds=1), first.id, vehicle.id, actor.user.id),
        )
    reversed_time = service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id)
    assert [record.id for record in reversed_time.services] == [latest_date.id, first.id, second.id, old.id]
    with native_database.connect(native_database.settings) as connection:
        connection.execute(
            "UPDATE public.service_records AS s SET created_at = %s FROM public.vehicles AS v "
            "WHERE s.id = ANY(%s) AND s.vehicle_id = %s AND v.id = s.vehicle_id AND v.user_id = %s",
            (first.created_at, [first.id, second.id], vehicle.id, actor.user.id),
        )
    tied = service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id)
    assert [record.id for record in tied.services] == [latest_date.id, second.id, first.id, old.id]


def test_result_is_prepared_while_uncommitted_and_returned_after_connection_close(native_database, actors, monkeypatch):
    actor = actors[0]
    vehicle = owned_vehicle(native_database, actor)
    request = reserved_service(native_database, actor, vehicle)
    connections, prepared = [], []

    @contextmanager
    def observe(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            connections.append(connection)
            yield connection

    def prepare(record):
        assert connections and not connections[-1].closed
        with native_database.connect(native_database.settings, read_only=True) as connection:
            assert connection.execute(
                "SELECT s.id FROM public.service_records AS s JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
                (record.id, vehicle.id, actor.user.id),
            ).fetchone() is None
        prepared.append(record)

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", observe)
        result = service_queries.create_service(native_database.settings, actor=actor, vehicle_id=vehicle.id,
                                                service=request, prepare_response=prepare)
    native_database.track_service(result.id, vehicle.id, actor.user.id, request)
    assert prepared == [result] and len(connections) == 1 and connections[0].closed
    assert service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id).services == [result]


def test_response_preparation_failure_rolls_back_real_insert(native_database, actors):
    actor = actors[0]
    vehicle = owned_vehicle(native_database, actor)
    before = vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id)
    request = reserved_service(native_database, actor, vehicle)

    def fail_preparation(record):
        raise RuntimeError("Synthetic response preparation failure")

    with pytest.raises(RuntimeError, match="Synthetic response preparation failure"):
        service_queries.create_service(native_database.settings, actor=actor, vehicle_id=vehicle.id,
                                       service=request, prepare_response=fail_preparation)
    assert service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id).services == []
    assert vehicle_queries.get_vehicle(native_database.settings, actor=actor, vehicle_id=vehicle.id) == before


def test_commit_failure_before_commit_rolls_back_and_closes(native_database, actors, monkeypatch):
    actor = actors[0]
    vehicle = owned_vehicle(native_database, actor)
    request = reserved_service(native_database, actor, vehicle)
    connections = []

    @contextmanager
    def fail_commit(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            connections.append(connection)
            yield connection
            raise psycopg.OperationalError("Synthetic failure before commit")

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", fail_commit)
        with pytest.raises(service_queries.ServiceUnavailableError):
            service_queries.create_service(native_database.settings, actor=actor, vehicle_id=vehicle.id, service=request)
    assert len(connections) == 1 and connections[0].closed
    assert service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id).services == []


def test_lost_commit_acknowledgment_recovers_exact_committed_service_before_parent_cleanup(native_database, actors, monkeypatch):
    actor = actors[0]
    vehicle = owned_vehicle(native_database, actor)
    request = reserved_service(native_database, actor, vehicle)
    connections = []

    @contextmanager
    def lose_acknowledgment(settings, *, read_only):
        with native_database.connect(settings, read_only=read_only) as connection:
            connections.append(connection)
            yield connection
        raise psycopg.OperationalError("Synthetic lost acknowledgment after real commit")

    with monkeypatch.context() as patches:
        patches.setattr(database, "connect_database", lose_acknowledgment)
        with pytest.raises(service_queries.ServiceUnavailableError):
            service_queries.create_service(native_database.settings, actor=actor, vehicle_id=vehicle.id, service=request)
    assert len(connections) == 1 and connections[0].closed
    saved = service_queries.list_services(native_database.settings, actor=actor, vehicle_id=vehicle.id).services
    assert len(saved) == 1 and not native_database._services
    service_id = saved[0].id
    native_database.cleanup()
    assert native_database.cleanup_verified and native_database.cleanup_service_count == 1
    assert native_database.cleanup_vehicle_count == 1 and native_database.cleanup_counts == (2, 2)
    with native_database.connect(native_database.settings, read_only=True) as connection:
        assert connection.execute("SELECT id FROM public.service_records WHERE id = %s", (service_id,)).fetchone() is None
        assert connection.execute("SELECT id FROM public.vehicles WHERE id = %s", (vehicle.id,)).fetchone() is None
