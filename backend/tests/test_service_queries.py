from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import psycopg
import pytest
from pydantic import ValidationError

from app import database, service_queries
from app.config import Settings, TEST_DATABASE
from app.schemas import RegistrationResponse
from app.service_schemas import ServiceCreate
from app.session_queries import AuthenticatedSession
from app.vehicle_queries import VehicleNotFoundError


pytestmark = pytest.mark.usefixtures("forbid_database")
NOW = datetime(2026, 11, 18, tzinfo=timezone.utc)


@pytest.fixture
def settings():
    return Settings("unused", 5432, TEST_DATABASE, "synthetic", "")


@pytest.fixture
def actor():
    return AuthenticatedSession(RegistrationResponse(id=7, email="synthetic@example.com", created_at=NOW), 11, NOW)


@pytest.fixture
def service():
    return ServiceCreate(service_date="2020-01-01", service_type="repair", description="Quote' -- \u00e9", cost="0.00")


@pytest.fixture
def row(service):
    return (456, 123, service.service_date, service.service_type, service.description,
            service.mileage, service.operating_hours, service.cost, service.notes, NOW)


@pytest.fixture
def transaction(monkeypatch, row):
    connection = Mock()
    events, failures = [], {}
    connection.execute.return_value.fetchone.side_effect = [(123,), row]
    connection.execute.return_value.fetchall.return_value = [row]

    @contextmanager
    def connect(settings, *, read_only):
        events.append(("open", read_only))
        try:
            yield connection
            events.append("commit")
            if "commit" in failures:
                raise failures["commit"]
        except BaseException:
            events.append("rollback")
            raise
        finally:
            events.append("close")
            if "close" in failures:
                raise failures["close"]

    monkeypatch.setattr(database, "connect_database", connect)
    return connection, events, failures


def call_query(operation, settings, actor, service, **kwargs):
    if operation == "list":
        return service_queries.list_services(settings, actor=actor, vehicle_id=123, **kwargs)
    return service_queries.create_service(settings, actor=actor, vehicle_id=123, service=service, **kwargs)


def test_list_scopes_parent_and_services_to_bound_actor_and_orders_newest_first(settings, actor, service, transaction):
    connection, events, _ = transaction
    result = call_query("list", settings, actor, service)
    parent, listing = [call.args for call in connection.execute.call_args_list]
    assert parent == ("SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s", (123, 7))
    sql, parameters = listing
    assert sql.startswith("SELECT s.id, s.vehicle_id, s.service_date, s.service_type, s.description, s.mileage, s.operating_hours, s.cost, s.notes, s.created_at ")
    assert "JOIN public.vehicles AS v ON v.id = s.vehicle_id" in sql
    assert "WHERE s.vehicle_id = %s AND v.user_id = %s" in sql
    assert sql.endswith("ORDER BY s.service_date DESC, s.created_at DESC, s.id DESC")
    assert parameters == (123, 7)
    assert result.vehicle_id == 123 and [record.id for record in result.services] == [456]
    assert events == [("open", True), "commit", "close"]


def test_owned_parent_with_no_services_returns_empty_list(settings, actor, service, transaction):
    connection, events, _ = transaction
    connection.execute.return_value.fetchall.return_value = []
    assert call_query("list", settings, actor, service).model_dump() == {"vehicle_id": 123, "services": []}
    assert events[-2:] == ["commit", "close"]


@pytest.mark.parametrize("operation", ["list", "create"])
def test_no_owned_parent_is_one_not_found_outcome_without_service_sql(settings, actor, service, transaction, operation):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.side_effect = [None]
    with pytest.raises(VehicleNotFoundError) as caught:
        call_query(operation, settings, actor, service)
    assert str(caught.value) == "Vehicle not found."
    connection.execute.assert_called_once_with(
        "SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s", (123, 7),
    )
    assert events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("mileage,hours,cost", [(None, None, None), ("0.0", None, "0.00"), (None, "0.0", "0.01"), ("99999999999.9", "12.3", "9999999999.99")])
def test_create_binds_exact_values_and_rechecks_owner_in_insert_select(settings, actor, transaction, mileage, hours, cost):
    connection, events, _ = transaction
    request = ServiceCreate(service_date="2020-02-29", service_type="maintenance", description="Quote' -- \u00e9",
                            mileage=mileage, operating_hours=hours, cost=cost, notes=" Multiline\nNotes ")
    returned = (456, 123, request.service_date, request.service_type, request.description,
                request.mileage, request.operating_hours, request.cost, request.notes, NOW)
    connection.execute.return_value.fetchone.side_effect = [(123,), returned]
    result = service_queries.create_service(settings, actor=actor, vehicle_id=123, service=request)
    sql, parameters = connection.execute.call_args.args
    assert sql == (
        "INSERT INTO public.service_records "
        "(vehicle_id, service_date, service_type, description, mileage, operating_hours, cost, notes) "
        "SELECT v.id, %s, %s, %s, %s, %s, %s, %s "
        "FROM public.vehicles AS v WHERE v.id = %s AND v.user_id = %s "
        "RETURNING id, vehicle_id, service_date, service_type, description, mileage, operating_hours, cost, notes, created_at"
    )
    assert parameters == (date(2020, 2, 29), "maintenance", request.description,
                          Decimal(mileage) if mileage is not None else None,
                          Decimal(hours) if hours is not None else None,
                          Decimal(cost) if cost is not None else None, "Multiline\nNotes", 123, 7)
    assert request.description not in sql
    assert all("UPDATE" not in call.args[0] for call in connection.execute.call_args_list)
    assert result.model_dump(mode="json")["cost"] == cost
    assert events == [("open", False), "commit", "close"]


def test_parent_disappearing_before_insert_returns_not_found_and_rolls_back(settings, actor, service, transaction):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.side_effect = [(123,), None]
    with pytest.raises(VehicleNotFoundError):
        call_query("create", settings, actor, service)
    assert events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("operation", ["list", "create"])
def test_response_preparation_happens_before_commit_and_return_after_close(settings, actor, service, transaction, operation):
    _, events, _ = transaction
    prepared = []

    def prepare(result):
        assert events == [("open", operation == "list")]
        prepared.append(result.model_dump(mode="json"))
        events.append("prepare")

    result = call_query(operation, settings, actor, service, prepare_response=prepare)
    assert prepared == [result.model_dump(mode="json")]
    assert events == [("open", operation == "list"), "prepare", "commit", "close"]


@pytest.mark.parametrize("operation", ["list", "create"])
@pytest.mark.parametrize("failure_at", ["parent", "business", "prepare", "commit", "close"])
@pytest.mark.parametrize("failure_type", [psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled])
def test_availability_errors_translate_after_cleanup_without_retry(settings, actor, service, row, transaction, operation, failure_at, failure_type, caplog):
    connection, events, failures = transaction
    failure = failure_type("Synthetic private driver details")
    options = {}
    if failure_at == "parent":
        connection.execute.side_effect = failure
    elif failure_at == "business":
        connection.execute.side_effect = [Mock(fetchone=Mock(return_value=(123,))), failure]
    elif failure_at == "prepare":
        options["prepare_response"] = Mock(side_effect=failure)
    else:
        failures[failure_at] = failure
    with pytest.raises(service_queries.ServiceUnavailableError) as caught:
        call_query(operation, settings, actor, service, **options)
    assert str(caught.value) == "Service history unavailable. Please try again."
    assert events[-1] == "close"
    if failure_at not in ("close",):
        assert events[-2] == "rollback"
    assert events.count(("open", operation == "list")) == 1
    assert connection.execute.call_count <= 2
    assert caplog.text == ""


@pytest.mark.parametrize("operation", ["list", "create"])
def test_open_failure_is_safe(settings, actor, service, monkeypatch, operation):
    connect = Mock(side_effect=psycopg.OperationalError("Synthetic private driver details"))
    monkeypatch.setattr(database, "connect_database", connect)
    with pytest.raises(service_queries.ServiceUnavailableError):
        call_query(operation, settings, actor, service)
    connect.assert_called_once()


@pytest.mark.parametrize("operation", ["list", "create"])
@pytest.mark.parametrize("bad_row", [(456,), (456, 999, date(2020, 1, 1), "repair", "Text", None, None, None, None, NOW), (456, 123, date(2020, 1, 1), "invalid", "Text", None, None, None, None, NOW)])
def test_invalid_or_wrong_parent_results_roll_back_before_success(settings, actor, service, transaction, operation, bad_row):
    connection, events, _ = transaction
    connection.execute.return_value.fetchone.side_effect = [(123,), bad_row]
    connection.execute.return_value.fetchall.return_value = [bad_row]
    with pytest.raises((RuntimeError, ValueError, ValidationError)):
        call_query(operation, settings, actor, service)
    assert "commit" not in events and events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("operation", ["list", "create"])
def test_public_serialization_failure_rolls_back(settings, actor, service, transaction, monkeypatch, operation):
    _, events, _ = transaction
    response_type = service_queries.ServiceListResponse if operation == "list" else service_queries.ServiceRecord
    monkeypatch.setattr(response_type, "model_dump", Mock(side_effect=RuntimeError("Synthetic serialization failure")))
    with pytest.raises(RuntimeError, match="Synthetic serialization failure"):
        call_query(operation, settings, actor, service)
    assert "commit" not in events and events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("operation", ["list", "create"])
def test_unexpected_callback_failure_remains_unexpected_and_rolls_back(settings, actor, service, transaction, operation):
    _, events, _ = transaction
    with pytest.raises(RuntimeError, match="Synthetic response preparation failure"):
        call_query(operation, settings, actor, service,
                   prepare_response=Mock(side_effect=RuntimeError("Synthetic response preparation failure")))
    assert "commit" not in events and events[-2:] == ["rollback", "close"]
