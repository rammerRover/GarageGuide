from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import Mock

import psycopg
import pytest
from pydantic import ValidationError

from app import database, vehicle_queries
from app.vehicle_schemas import ReadingConfirmationRequired, Vehicle, VehiclePatch
from test_vehicle_queries import NOW, PUBLIC_COLUMNS, actor, settings, transaction


pytestmark = pytest.mark.usefixtures("forbid_database")


def stored_row(**changes):
    fields = dict(zip(vehicle_queries.PUBLIC_FIELDS,
                      (42, 2020, "Synthetic", "Original", "V8", "Car",
                       Decimal("1000.0"), Decimal("10.0"), NOW, NOW), strict=True))
    fields.update(changes)
    return tuple(fields[name] for name in vehicle_queries.PUBLIC_FIELDS)


def arrange(connection, patch, current=None):
    current = stored_row() if current is None else current
    values = dict(zip(vehicle_queries.PUBLIC_FIELDS, current, strict=True))
    values.update(patch.changes())
    returned = tuple(values[name] for name in vehicle_queries.PUBLIC_FIELDS)
    connection.execute.side_effect = [Mock(fetchone=lambda: current), Mock(fetchone=lambda: returned)]
    return returned


def invoke(operation, settings, actor, patch=None, **options):
    if operation == "get":
        return vehicle_queries.get_vehicle(settings, actor=actor, vehicle_id=42, **options)
    return vehicle_queries.update_vehicle(
        settings, actor=actor, vehicle_id=42, patch=patch or VehiclePatch(model="Changed"), **options,
    )


def test_detail_is_one_bound_owner_scoped_read_only_query(settings, actor, transaction):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.return_value = stored_row()
    result = invoke("get", settings, actor)
    connection.execute.assert_called_once_with(
        f"SELECT {PUBLIC_COLUMNS} FROM public.vehicles WHERE id = %s AND user_id = %s", (42, 7),
    )
    assert result.id == 42 and set(result.model_dump()) == set(vehicle_queries.PUBLIC_FIELDS)
    assert events == [("open", True), "commit", "close"]


@pytest.mark.parametrize("operation", ["get", "update"])
def test_missing_or_foreign_row_has_no_existence_probe_and_closes(settings, actor, transaction, operation):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.return_value = None
    with pytest.raises(vehicle_queries.VehicleNotFoundError) as caught:
        invoke(operation, settings, actor)
    assert str(caught.value) == "Vehicle not found."
    assert connection.execute.call_count == 1
    assert connection.execute.call_args.args[1] == (42, 7)
    assert events == [("open", operation == "get"), "rollback", "close"]


def test_lock_precedes_fresh_confirmation_and_all_variable_values_are_bound(settings, actor, transaction, monkeypatch):
    connection, events, _ = transaction
    patch = VehiclePatch(make="Quote' --", mileage="900", reading_confirmation={"mileage": "1000"})
    arrange(connection, patch)
    original = vehicle_queries.require_reading_confirmation

    def compare(current, supplied):
        connection.execute.assert_called_once_with(
            f"SELECT {PUBLIC_COLUMNS} FROM public.vehicles WHERE id = %s AND user_id = %s FOR UPDATE", (42, 7),
        )
        assert current.mileage == Decimal("1000") and supplied is patch
        original(current, supplied)

    monkeypatch.setattr(vehicle_queries, "require_reading_confirmation", compare)
    result = invoke("update", settings, actor, patch)
    sql, parameters = connection.execute.call_args.args
    assert sql == (
        "UPDATE public.vehicles SET year = %s, make = %s, model = %s, engine = %s, "
        "vehicle_type = %s, mileage = %s, operating_hours = %s, "
        "readings_updated_at = CASE WHEN %s THEN clock_timestamp() ELSE readings_updated_at END "
        f"WHERE id = %s AND user_id = %s RETURNING {PUBLIC_COLUMNS}"
    )
    assert parameters == (2020, "Quote' --", "Original", "V8", "Car", Decimal("900"), Decimal("10"), True, 42, 7)
    assert "Quote' --" not in sql and "reading_confirmation" not in sql
    assert result.make == "Quote' --" and result.created_at == NOW
    assert events == [("open", False), "commit", "close"]


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("new", [None, "0", "9"])
def test_missing_confirmation_rolls_back_without_any_partial_update(settings, actor, transaction, field, new):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.return_value = stored_row()
    with pytest.raises(ReadingConfirmationRequired) as caught:
        invoke("update", settings, actor, VehiclePatch.model_validate({"make": "Changed", field: new}))
    assert caught.value.fields == (field,) and connection.execute.call_count == 1
    assert events == [("open", False), "rollback", "close"]


@pytest.mark.parametrize("current,required", [("1200", True), ("800", False), ("900", False), (None, False)])
def test_stale_confirmation_uses_locked_value_and_never_writes(settings, actor, transaction, current, required):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.return_value = stored_row(mileage=None if current is None else Decimal(current))
    patch = VehiclePatch(model="Changed", mileage="900", reading_confirmation={"mileage": "1000"})
    with pytest.raises(ReadingConfirmationRequired) as caught:
        invoke("update", settings, actor, patch)
    assert caught.value.fields == (("mileage",) if required else ())
    assert connection.execute.call_count == 1 and events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("old,new,changes_time", [(None, "0", True), ("0", None, True), ("10", "11", True), ("10", "10.0", False), (None, None, False)])
def test_timestamp_flag_uses_null_safe_actual_reading_change(settings, actor, transaction, field, old, new, changes_time):
    connection, events, _ = transaction
    current = stored_row(**{field: None if old is None else Decimal(old)})
    fields = {"model": "Changed", field: new}
    if old is not None and new is None:
        fields["reading_confirmation"] = {field: old}
    patch = VehiclePatch.model_validate(fields)
    arrange(connection, patch, current)
    result = invoke("update", settings, actor, patch)
    assert connection.execute.call_args.args[1][-3:] == (changes_time, 42, 7)
    assert result.created_at == NOW and events[-2:] == ["commit", "close"]


def test_omitted_legacy_values_are_merged_from_raw_locked_row(settings, actor, transaction):
    connection, _, _ = transaction
    patch = VehiclePatch(model="Changed")
    arrange(connection, patch, stored_row(year=1, make="  Stored make  ", engine="  V8  "))
    result = invoke("update", settings, actor, patch)
    assert connection.execute.call_args.args[1][:5] == (1, "  Stored make  ", "Changed", "  V8  ", "Car")
    assert result.year == 1


@pytest.mark.parametrize("fields", [{"make": "Synthetic"}, {"mileage": "01000.0"}, {"operating_hours": "10", "reading_confirmation": {"operating_hours": "10"}}])
def test_valid_noop_prepares_and_commits_without_update(settings, actor, transaction, fields):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.return_value = stored_row()

    def prepare(result):
        assert events == [("open", False)]
        assert result.readings_updated_at == NOW
        events.append("prepare")

    invoke("update", settings, actor, VehiclePatch.model_validate(fields), prepare_response=prepare)
    assert connection.execute.call_count == 1
    assert events == [("open", False), "prepare", "commit", "close"]


@pytest.mark.parametrize("operation", ["get", "update"])
def test_preparation_is_inside_transaction_and_success_returns_only_after_close(settings, actor, transaction, operation, monkeypatch):
    connection, events, _ = transaction
    patch = VehiclePatch(model="Changed")
    arrange(connection, patch)
    original = Vehicle.model_dump

    def serialize(self, **options):
        assert "commit" not in events and "close" not in events
        events.append("serialize")
        return original(self, **options)

    monkeypatch.setattr(Vehicle, "model_dump", serialize)
    invoke(operation, settings, actor, patch, prepare_response=lambda result: events.append("prepare"))
    assert events == [("open", operation == "get"), "serialize", "prepare", "commit", "close"]


@pytest.mark.parametrize("operation", ["get", "update"])
@pytest.mark.parametrize("failure_at", ["select", "prepare", "commit", "close"])
@pytest.mark.parametrize("failure_type", [psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled, psycopg.errors.LockNotAvailable])
def test_availability_translation_happens_after_cleanup_without_retry(settings, actor, transaction, monkeypatch, operation, failure_at, failure_type, caplog):
    connection, events, commit_errors = transaction
    failure = failure_type("Synthetic private SQL and driver details")
    arrange(connection, VehiclePatch(model="Changed"))
    callback = None
    if failure_at == "select":
        connection.execute.side_effect = failure
    elif failure_at == "prepare":
        callback = Mock(side_effect=failure)
    elif failure_at == "commit":
        commit_errors.append(failure)
    else:
        original = database.connect_database
        @contextmanager
        def fail_after_close(settings, *, read_only):
            with original(settings, read_only=read_only) as opened:
                yield opened
            raise failure

        monkeypatch.setattr(database, "connect_database", fail_after_close)
    with pytest.raises(vehicle_queries.VehicleUnavailableError) as caught:
        invoke(operation, settings, actor, prepare_response=callback)
    assert events[-1] == "close" and sum(isinstance(event, tuple) for event in events) == 1
    if failure_at != "close":
        assert events[-2:] == ["rollback", "close"]
    assert str(caught.value) == "Vehicles unavailable. Please try again." and not caplog.text


def test_update_failure_after_locked_comparison_rolls_back(settings, actor, transaction):
    connection, events, _ = transaction
    connection.execute.side_effect = [Mock(fetchone=lambda: stored_row()), psycopg.OperationalError("Synthetic update failure")]
    with pytest.raises(vehicle_queries.VehicleUnavailableError):
        invoke("update", settings, actor)
    assert connection.execute.call_count == 2 and events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("operation", ["get", "update"])
def test_open_failure_is_safely_translated(settings, actor, monkeypatch, operation):
    connect = Mock(side_effect=psycopg.OperationalError("Synthetic private failure"))
    monkeypatch.setattr(database, "connect_database", connect)
    with pytest.raises(vehicle_queries.VehicleUnavailableError):
        invoke(operation, settings, actor)
    connect.assert_called_once_with(settings, read_only=operation == "get")


@pytest.mark.parametrize("operation", ["get", "update"])
def test_unexpected_error_is_not_reclassified_as_availability(settings, actor, transaction, operation):
    connection, events, _ = transaction
    connection.execute.side_effect = RuntimeError("Synthetic unexpected failure")
    with pytest.raises(RuntimeError, match="Synthetic unexpected failure"):
        invoke(operation, settings, actor)
    assert events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("bad", [None, (42,), stored_row(year=0)])
def test_invalid_update_returning_rolls_back(settings, actor, transaction, bad):
    connection, events, _ = transaction
    connection.execute.side_effect = [Mock(fetchone=lambda: stored_row()), Mock(fetchone=lambda: bad)]
    with pytest.raises((RuntimeError, ValueError, ValidationError)):
        invoke("update", settings, actor)
    assert events[-2:] == ["rollback", "close"]
