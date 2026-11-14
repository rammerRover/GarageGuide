from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import psycopg
import pytest
from pydantic import ValidationError

from app import database, vehicle_queries
from app.config import Settings, TEST_DATABASE
from app.schemas import RegistrationResponse
from app.session_queries import AuthenticatedSession
from app.vehicle_schemas import Vehicle, VehicleCreate


pytestmark = pytest.mark.usefixtures("forbid_database")
NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)
PUBLIC_COLUMNS = "id, year, make, model, engine, vehicle_type, mileage, operating_hours, readings_updated_at, created_at"


@pytest.fixture
def settings():
    return Settings("unused", 5432, TEST_DATABASE, "synthetic", "")


@pytest.fixture
def actor():
    return AuthenticatedSession(
        RegistrationResponse(id=7, email="synthetic@example.com", created_at=NOW), 11, NOW,
    )


@pytest.fixture
def fields():
    return {"year": 2020, "make": "Quote' --", "model": "Synthetic", "vehicle_type": "Custom"}


@pytest.fixture
def row():
    return (42, 2020, "Quote' --", "Synthetic", None, "Custom", None, None, None, NOW)


@pytest.fixture
def transaction(monkeypatch):
    connection = Mock()
    events, commit_errors = [], []

    @contextmanager
    def connect(settings, *, read_only):
        events.append(("open", read_only))
        try:
            yield connection
            events.append("commit")
            if commit_errors:
                raise commit_errors[0]
        except BaseException:
            events.append("rollback")
            raise
        finally:
            events.append("close")

    monkeypatch.setattr(database, "connect_database", connect)
    return connection, events, commit_errors


def test_list_uses_only_bound_actor_and_explicit_public_columns(settings, actor, row, transaction):
    connection, events, _ = transaction
    connection.execute.return_value.fetchall.return_value = [row]
    result = vehicle_queries.list_vehicles(settings, actor=actor)
    connection.execute.assert_called_once_with(
        f"SELECT {PUBLIC_COLUMNS} FROM public.vehicles "
        "WHERE user_id = %s ORDER BY created_at DESC, id DESC", (7,),
    )
    assert [vehicle.id for vehicle in result.vehicles] == [42]
    assert events == [("open", True), "commit", "close"]


def test_empty_owned_list_is_success(settings, actor, transaction):
    connection, events, _ = transaction
    connection.execute.return_value.fetchall.return_value = []
    assert vehicle_queries.list_vehicles(settings, actor=actor).model_dump() == {"vehicles": []}
    assert events[-2:] == ["commit", "close"]


@pytest.mark.parametrize(
    ("mileage", "hours", "known"),
    [(None, None, False), ("0.0", None, True), (None, "0.0", True), ("123.4", "56.7", True)],
)
def test_create_binds_actor_decimal_null_and_database_timestamp(
    settings, actor, fields, row, transaction, mileage, hours, known,
):
    connection, events, _ = transaction
    request = VehicleCreate(**fields, mileage=mileage, operating_hours=hours)
    returned = (*row[:6], request.mileage, request.operating_hours, NOW if known else None, NOW)
    connection.execute.return_value.fetchone.return_value = returned
    result = vehicle_queries.create_vehicle(settings, actor=actor, vehicle=request)
    sql, parameters = connection.execute.call_args.args
    assert sql == (
        "INSERT INTO public.vehicles "
        "(user_id, year, make, model, engine, vehicle_type, mileage, operating_hours, readings_updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END) "
        f"RETURNING {PUBLIC_COLUMNS}"
    )
    assert parameters == (7, 2020, "Quote' --", "Synthetic", None, "Custom",
                          Decimal(mileage) if mileage is not None else None,
                          Decimal(hours) if hours is not None else None, known)
    assert fields["make"] not in sql
    assert "user_id" not in result.model_dump()
    assert events == [("open", False), "commit", "close"]


def test_create_serializes_public_result_before_commit_and_returns_after_close(
    settings, actor, fields, row, transaction, monkeypatch,
):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.return_value = row
    original = Vehicle.model_dump

    def prepare(self, **kwargs):
        assert events == [("open", False)]
        events.append("prepare-public-result")
        return original(self, **kwargs)

    monkeypatch.setattr(Vehicle, "model_dump", prepare)
    result = vehicle_queries.create_vehicle(settings, actor=actor, vehicle=VehicleCreate(**fields))
    assert result.id == 42
    assert events == [("open", False), "prepare-public-result", "commit", "close"]


@pytest.mark.parametrize("operation", ["list", "create"])
@pytest.mark.parametrize("failure_at", ["execute", "commit", "prepare"])
@pytest.mark.parametrize("failure_type", [psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled])
def test_availability_failures_translate_after_context_cleanup(
    settings, actor, fields, row, transaction, monkeypatch, operation, failure_at, failure_type, caplog,
):
    connection, events, commit_errors = transaction
    failure = failure_type("Synthetic private driver details")
    connection.execute.return_value.fetchone.return_value = row
    connection.execute.return_value.fetchall.return_value = [row]
    if failure_at == "execute":
        connection.execute.side_effect = failure
    elif failure_at == "commit":
        commit_errors.append(failure)
    else:
        monkeypatch.setattr(Vehicle, "model_dump", Mock(side_effect=failure))
        # List serialization is owned by the enclosing response model.
        monkeypatch.setattr(vehicle_queries.VehicleListResponse, "model_dump", Mock(side_effect=failure))
    with pytest.raises(vehicle_queries.VehicleUnavailableError) as caught:
        if operation == "list":
            vehicle_queries.list_vehicles(settings, actor=actor)
        else:
            vehicle_queries.create_vehicle(settings, actor=actor, vehicle=VehicleCreate(**fields))
    assert events[-2:] == ["rollback", "close"]
    assert str(caught.value) == "Vehicles unavailable. Please try again."
    assert caplog.text == ""


@pytest.mark.parametrize("operation", ["list", "create"])
def test_open_failure_is_safely_translated_without_claiming_success(settings, actor, fields, monkeypatch, operation):
    monkeypatch.setattr(database, "connect_database", Mock(side_effect=psycopg.OperationalError("Synthetic failure")))
    with pytest.raises(vehicle_queries.VehicleUnavailableError):
        if operation == "list":
            vehicle_queries.list_vehicles(settings, actor=actor)
        else:
            vehicle_queries.create_vehicle(settings, actor=actor, vehicle=VehicleCreate(**fields))


@pytest.mark.parametrize("bad_row", [None, (42,), (42, 0, "Honda", "Synthetic", None, "Car", None, None, None, NOW)])
def test_invalid_returned_record_rolls_back_before_commit(settings, actor, fields, transaction, bad_row):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.return_value = bad_row
    with pytest.raises((RuntimeError, ValueError, ValidationError)):
        vehicle_queries.create_vehicle(settings, actor=actor, vehicle=VehicleCreate(**fields))
    assert events == [("open", False), "rollback", "close"]


@pytest.mark.parametrize("operation", ["list", "create"])
def test_unexpected_failures_remain_unexpected_and_close(settings, actor, fields, transaction, operation):
    connection, events, _ = transaction
    connection.execute.side_effect = RuntimeError("Synthetic unexpected failure")
    with pytest.raises(RuntimeError, match="Synthetic unexpected failure"):
        if operation == "list":
            vehicle_queries.list_vehicles(settings, actor=actor)
        else:
            vehicle_queries.create_vehicle(settings, actor=actor, vehicle=VehicleCreate(**fields))
    assert events[-2:] == ["rollback", "close"]
