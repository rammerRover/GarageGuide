from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import psycopg
import pytest
from pydantic import ValidationError

from app import database, service_queries
from app.service_schemas import ServicePatch, ServiceRemovalRequest
from test_service_queries import actor, row, service, settings, transaction


pytestmark = pytest.mark.usefixtures("forbid_database")


def arrange(transaction, row, operation, *, linked=(False, False), new_row=None):
    connection, events, failures = transaction
    rows = [row]
    if operation != "get":
        rows.append(linked)
        rows.append((456, 123) if operation == "remove" else new_row or (*row[:8], "Corrected notes", row[9]))
    connection.execute.return_value.fetchone.side_effect = rows
    return connection, events, failures


def run(operation, settings, actor, **options):
    common = {"actor": actor, "vehicle_id": 123, "service_id": 456, **options}
    if operation == "get":
        return service_queries.get_service(settings, **common)
    if operation == "update":
        common.setdefault("patch", ServicePatch(notes="Corrected notes"))
        return service_queries.update_service(settings, **common)
    common.setdefault("confirmation", ServiceRemovalRequest(confirm_removal=True))
    return service_queries.remove_service(settings, **common)


@pytest.mark.parametrize("operation", ["get", "update", "remove"])
def test_every_operation_scopes_service_parent_and_actor_and_locks_mutations(settings, actor, row, transaction, operation):
    connection, events, _ = arrange(transaction, row, operation)
    result = run(operation, settings, actor)
    calls = [call.args for call in connection.execute.call_args_list]
    sql, parameters = calls[0]
    assert sql.startswith("SELECT s.id, s.vehicle_id, s.service_date, s.service_type, s.description, s.mileage, s.operating_hours, s.cost, s.notes, s.created_at ")
    assert "JOIN public.vehicles AS v ON v.id = s.vehicle_id" in sql
    assert "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s" in sql
    assert sql.endswith(" FOR UPDATE OF s") == (operation != "get")
    assert parameters == (456, 123, 7)
    if operation != "get":
        assert calls[1][1] == (456, 123, 7)
        assert "maintenance_completions" in calls[1][0] and "service_parts" in calls[1][0]
        assert "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s" in calls[1][0]
        assert calls[2][1][-3:] == (456, 123, 7)
        assert "v.user_id = %s" in calls[2][0] and "s.vehicle_id = %s" in calls[2][0]
    assert result.id == 456 and result.vehicle_id == 123
    assert events == [("open", operation == "get"), "commit", "close"]


@pytest.mark.parametrize("operation", ["get", "update", "remove"])
def test_no_owned_row_produces_same_not_found_without_link_checks_or_writes(settings, actor, row, transaction, operation):
    connection, events, _ = arrange(transaction, row, operation)
    connection.execute.return_value.fetchone.side_effect = [None]
    with pytest.raises(service_queries.ServiceNotFoundError) as caught:
        run(operation, settings, actor)
    assert str(caught.value) == "Service record not found."
    assert connection.execute.call_count == 1
    assert events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("operation", ["update", "remove"])
def test_completion_link_blocks_entire_mutation_without_preparing_success(settings, actor, row, transaction, operation):
    connection, events, _ = arrange(transaction, row, operation, linked=(True, False))
    prepared = Mock()
    expected = service_queries.ServiceEditBlockedError if operation == "update" else service_queries.ServiceRemovalBlockedError
    with pytest.raises(expected) as caught:
        run(operation, settings, actor, prepare_response=prepared)
    assert str(caught.value) == ("Service record is linked to maintenance completion and cannot be changed."
                                 if operation == "update" else "Service record has linked data and cannot be removed.")
    assert connection.execute.call_count == 2 and events[-2:] == ["rollback", "close"]
    prepared.assert_not_called()


def test_part_snapshot_blocks_removal_but_not_edit(settings, actor, row, transaction):
    connection, _, _ = arrange(transaction, row, "update", linked=(False, True))
    assert run("update", settings, actor).notes == "Corrected notes"
    assert connection.execute.call_count == 3
    arrange(transaction, row, "remove", linked=(False, True))
    connection.execute.reset_mock()
    with pytest.raises(service_queries.ServiceRemovalBlockedError):
        run("remove", settings, actor)
    assert connection.execute.call_count == 2


def test_noop_succeeds_without_link_query_or_update(settings, actor, row, transaction):
    connection, events, _ = arrange(transaction, row, "update")
    result = run("update", settings, actor, patch=ServicePatch(cost="0.00", description=row[4]))
    assert result.cost == Decimal("0.00")
    assert connection.execute.call_count == 1
    assert events[-2:] == ["commit", "close"]


def test_update_preserves_raw_omitted_values_from_locked_row_and_binds_exact_changes(settings, actor, row, transaction):
    stored = dict(zip(service_queries.PUBLIC_FIELDS, row, strict=True))
    stored.update(service_date=date(2099, 1, 1), description="  Legacy description  ", mileage=Decimal("100.0"), operating_hours=Decimal("10.0"))
    raw = tuple(stored[name] for name in service_queries.PUBLIC_FIELDS)
    patch = ServicePatch(mileage="0", operating_hours=None, cost=None, notes=" \t ")
    merged = {**stored, **patch.changes()}
    updated = tuple(merged[name] for name in service_queries.PUBLIC_FIELDS)
    connection, _, _ = arrange(transaction, raw, "update", new_row=updated)
    result = run("update", settings, actor, patch=patch)
    sql, parameters = connection.execute.call_args.args
    assert parameters == (date(2099, 1, 1), "repair", "  Legacy description  ", Decimal("0"), None, None, None, 456, 123, 7)
    assert "UPDATE public.service_records AS s" in sql
    assert "created_at =" not in sql and "readings_updated_at" not in sql
    assert result.service_date == date(2099, 1, 1) and result.mileage == Decimal("0.0")
    assert result.created_at == row[9]


def test_removal_requires_confirmation_before_opening_connection(settings, actor, monkeypatch):
    connect = Mock()
    monkeypatch.setattr(database, "connect_database", connect)
    confirmation = ServiceRemovalRequest(confirm_removal=True)
    confirmation.confirm_removal = False
    with pytest.raises(ValueError, match="Confirm removal with true"):
        run("remove", settings, actor, confirmation=confirmation)
    connect.assert_not_called()


@pytest.mark.parametrize("operation", ["get", "update", "remove"])
def test_response_preparation_precedes_commit_and_success_follows_close(settings, actor, row, transaction, operation):
    _, events, _ = arrange(transaction, row, operation)
    prepared = []
    def prepare(result):
        assert events == [("open", operation == "get")]
        prepared.append(result.model_dump(mode="json"))
        events.append("prepared")
    result = run(operation, settings, actor, prepare_response=prepare)
    assert prepared == [result.model_dump(mode="json")]
    assert events[-3:] == ["prepared", "commit", "close"]


@pytest.mark.parametrize("operation", ["update", "remove"])
@pytest.mark.parametrize("links", [None, (), (False,), (False, False, False), (0, False), (False, None)])
def test_invalid_link_results_fail_closed_without_writes(settings, actor, row, transaction, operation, links):
    connection, events, _ = arrange(transaction, row, operation, linked=links)
    with pytest.raises((RuntimeError, service_queries.ServiceNotFoundError)):
        run(operation, settings, actor)
    assert connection.execute.call_count == 2 and events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("operation", ["get", "update", "remove"])
@pytest.mark.parametrize("bad_row", [(456,), (999, 123), (456, 999)])
def test_invalid_or_mismatched_owned_row_rolls_back(settings, actor, row, transaction, operation, bad_row):
    connection, events, _ = arrange(transaction, row, operation)
    connection.execute.return_value.fetchone.side_effect = [bad_row]
    with pytest.raises((RuntimeError, ValidationError, ValueError)):
        run(operation, settings, actor)
    assert events[-2:] == ["rollback", "close"] and "commit" not in events


@pytest.mark.parametrize("operation", ["update", "remove"])
@pytest.mark.parametrize("bad", [None, (999, 123), (456, 999)])
def test_missing_or_mismatched_write_result_cannot_claim_success(settings, actor, row, transaction, operation, bad):
    connection, events, _ = arrange(transaction, row, operation)
    connection.execute.return_value.fetchone.side_effect = [row, (False, False), bad]
    with pytest.raises((RuntimeError, service_queries.ServiceNotFoundError)):
        run(operation, settings, actor)
    assert events[-2:] == ["rollback", "close"] and "commit" not in events


@pytest.mark.parametrize("operation", ["get", "update", "remove"])
@pytest.mark.parametrize("failure_at", ["read", "prepare", "commit", "close"])
@pytest.mark.parametrize("failure_type", [psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled])
def test_availability_failures_translate_after_cleanup_without_retry(settings, actor, row, transaction, operation, failure_at, failure_type, caplog):
    connection, events, failures = arrange(transaction, row, operation)
    failure = failure_type("Synthetic private driver details")
    options = {}
    if failure_at == "read":
        connection.execute.side_effect = failure
    elif failure_at == "prepare":
        options["prepare_response"] = Mock(side_effect=failure)
    else:
        failures[failure_at] = failure
    with pytest.raises(service_queries.ServiceUnavailableError) as caught:
        run(operation, settings, actor, **options)
    assert str(caught.value) == "Service history unavailable. Please try again."
    assert events[-1] == "close" and events.count(("open", operation == "get")) == 1
    if failure_at != "close":
        assert events[-2] == "rollback"
    assert caplog.text == ""


@pytest.mark.parametrize("operation", ["get", "update", "remove"])
def test_unexpected_response_failure_rolls_back_without_translation(settings, actor, row, transaction, operation):
    _, events, _ = arrange(transaction, row, operation)
    with pytest.raises(RuntimeError, match="Synthetic response failure"):
        run(operation, settings, actor, prepare_response=Mock(side_effect=RuntimeError("Synthetic response failure")))
    assert events[-2:] == ["rollback", "close"] and "commit" not in events
