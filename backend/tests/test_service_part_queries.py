from contextlib import contextmanager
from unittest.mock import Mock

import psycopg
import pytest
from pydantic import ValidationError

from app import database, service_part_queries as queries
from app.service_part_schemas import (
    CatalogPartLookup, CatalogPartPreview, CatalogServicePartCreate, ManualServicePartCreate,
    ServicePartRemovalRequest,
)
from app.service_queries import ServiceNotFoundError
from app.vehicle_queries import VehicleNotFoundError
from test_service_queries import actor, settings


pytestmark = pytest.mark.usefixtures("forbid_database")
CATALOG = (22, "Maker", "EX-123", "Catalog filter", "Filters")
SNAPSHOT = (789, 456, None, "Manual filter", None, None, 1, None)
OPERATIONS = ["list", "lookup", "manual", "catalog", "remove"]


def request_part(operation):
    if operation == "catalog":
        return CatalogServicePartCreate(source="catalog", preview=CatalogPartPreview(
            **dict(zip(queries.CATALOG_FIELDS, CATALOG, strict=True))))
    return ManualServicePartCreate(source="manual", name="Manual filter")


def invoke(operation, settings, actor, **options):
    common = {"actor": actor, "vehicle_id": 123, "service_id": 456, **options}
    if operation == "list":
        return queries.list_service_parts(settings, **common)
    if operation == "lookup":
        return queries.lookup_catalog_part(settings, lookup=CatalogPartLookup(manufacturer="Maker", part_number="EX-123"), **common)
    if operation == "remove":
        return queries.remove_service_part(settings, snapshot_id=789,
                                           confirmation=ServicePartRemovalRequest(confirm_removal=True), **common)
    return queries.attach_service_part(settings, part=request_part(operation), **common)


@pytest.fixture
def transaction(monkeypatch):
    connection, events, failures = Mock(), [], {}

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

    connector = Mock(side_effect=connect)
    monkeypatch.setattr(database, "connect_database", connector)

    def configure(operation):
        rows = [(123,), (456, 123)]
        if operation in ("lookup", "catalog"):
            rows.append(CATALOG)
        if operation in ("manual", "catalog"):
            rows.append(SNAPSHOT if operation == "manual" else (789, 456, 22, "Catalog filter", "EX-123", "Maker", 1, None))
        if operation == "remove":
            rows.append((789, 456))
        connection.execute.return_value.fetchone.side_effect = rows
        connection.execute.return_value.fetchall.return_value = [SNAPSHOT]

    return connection, events, failures, connector, configure


@pytest.mark.parametrize("operation", OPERATIONS)
def test_owner_parameters_explicit_columns_and_transaction_order(settings, actor, transaction, operation):
    connection, events, _, connector, configure = transaction
    configure(operation)
    prepared = []
    def prepare(result):
        assert events == [("open", operation in ("list", "lookup"))]
        prepared.append(result.model_dump(mode="json"))
    result = invoke(operation, settings, actor, prepare_response=prepare)
    assert prepared == [result.model_dump(mode="json")]
    assert events == [("open", operation in ("list", "lookup")), "commit", "close"]
    connector.assert_called_once()
    calls = [call.args for call in connection.execute.call_args_list]
    assert calls[0] == ("SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s", (123, 7))
    service_sql, service_params = calls[1]
    assert service_params == (456, 123, 7)
    assert "s.id = %s AND s.vehicle_id = %s AND v.user_id = %s" in service_sql
    assert service_sql.endswith(" FOR UPDATE OF s") == (operation not in ("list", "lookup"))
    for sql, parameters in calls[2:]:
        assert "s.vehicle_id = %s" in sql and "v.user_id = %s" in sql
        assert parameters[-3:] == (456, 123, 7) or operation == "remove" and parameters == (789, 456, 123, 7)
        assert "SELECT *" not in sql and "RETURNING *" not in sql
    if operation == "list":
        assert calls[-1][0].endswith("ORDER BY p.id ASC")
        assert result.parts[0].id == 789
    if operation in ("catalog", "lookup"):
        assert calls[2][1] == ("Maker", "EX-123", 456, 123, 7)
        assert calls[2][0].endswith(" FOR SHARE OF p") == (operation == "catalog")


def test_empty_owned_service_returns_ordinary_empty_list(settings, actor, transaction):
    connection, _, _, _, configure = transaction
    configure("list")
    connection.execute.return_value.fetchall.return_value = []
    assert invoke("list", settings, actor).model_dump(mode="json") == {
        "vehicle_id": 123, "service_record_id": 456, "parts": [],
    }


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("missing", ["vehicle", "service"])
def test_missing_or_foreign_parent_stops_before_catalog_or_child_sql(settings, actor, transaction, operation, missing):
    connection, events, _, _, _ = transaction
    connection.execute.return_value.fetchone.side_effect = [None] if missing == "vehicle" else [(123,), None]
    expected = VehicleNotFoundError if missing == "vehicle" else ServiceNotFoundError
    with pytest.raises(expected):
        invoke(operation, settings, actor)
    assert connection.execute.call_count == (1 if missing == "vehicle" else 2)
    assert events[-2:] == ["rollback", "close"]


def test_manual_insert_has_no_catalog_dependency_and_binds_values(settings, actor, transaction):
    connection, _, _, _, configure = transaction
    configure("manual")
    part = ManualServicePartCreate(source="manual", name="Filter' -- \ufeff", notes="Interior\nText", quantity=2147483647)
    row = (789, 456, None, part.name, None, None, part.quantity, part.notes)
    connection.execute.return_value.fetchone.side_effect = [(123,), (456, 123), row]
    result = queries.attach_service_part(settings, actor=actor, vehicle_id=123, service_id=456, part=part)
    sql, parameters = connection.execute.call_args.args
    assert parameters == (None, part.name, None, None, 2147483647, part.notes, 456, 123, 7)
    assert part.name not in sql and part.notes not in sql
    assert not any("public.parts " in call.args[0] for call in connection.execute.call_args_list)
    assert result.model_dump(mode="json") == dict(zip(queries.PUBLIC_FIELDS, row, strict=True))


def test_catalog_identity_bindings_use_the_locked_row_not_the_preview(settings, actor, transaction):
    connection, _, _, _, _ = transaction
    server = tuple(value.encode().decode() if isinstance(value, str) else value for value in CATALOG)
    compared = CatalogPartPreview(**{key: value.encode().decode() if isinstance(value, str) else value
                                    for key, value in zip(queries.CATALOG_FIELDS, server, strict=True)})
    assert compared.name == server[3] and compared.name is not server[3]
    connection.execute.return_value.fetchone.side_effect = [
        (123,), (456, 123), server, (789, 456, 22, server[3], server[2], server[1], 1, None),
    ]
    queries.attach_service_part(settings, actor=actor, vehicle_id=123, service_id=456,
                                part=CatalogServicePartCreate(source="catalog", preview=compared))
    parameters = connection.execute.call_args.args[1]
    assert parameters[1] is server[3] and parameters[2] is server[2] and parameters[3] is server[1]


@pytest.mark.parametrize("field", range(5))
def test_every_changed_preview_identity_field_rejects_atomically(settings, actor, transaction, field):
    connection, events, _, _, _ = transaction
    row = list(CATALOG)
    row[field] = 23 if field == 0 else row[field] + " changed"
    connection.execute.return_value.fetchone.side_effect = [(123,), (456, 123), tuple(row)]
    with pytest.raises(queries.CatalogPreviewConflictError):
        invoke("catalog", settings, actor)
    assert connection.execute.call_count == 3
    assert not any(call.args[0].startswith(("INSERT", "UPDATE", "DELETE")) for call in connection.execute.call_args_list)
    assert events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("operation", ["lookup", "catalog"])
def test_catalog_miss_is_safe_and_never_silently_manual(settings, actor, transaction, operation):
    connection, events, _, _, _ = transaction
    connection.execute.return_value.fetchone.side_effect = [(123,), (456, 123), None]
    expected = queries.CatalogPartNotFoundError if operation == "lookup" else queries.CatalogPreviewConflictError
    with pytest.raises(expected):
        invoke(operation, settings, actor)
    assert connection.execute.call_count == 3 and events[-2:] == ["rollback", "close"]


def test_lookup_pair_is_not_casefolded_trimmed_or_interpolated(settings, actor, transaction):
    connection, _, _, _, _ = transaction
    pair = CatalogPartLookup(manufacturer=" Maker' -- ", part_number="Ex-123 \ufeff")
    row = (22, pair.manufacturer, pair.part_number, "Name", "Category")
    connection.execute.return_value.fetchone.side_effect = [(123,), (456, 123), row]
    result = queries.lookup_catalog_part(settings, actor=actor, vehicle_id=123, service_id=456, lookup=pair)
    sql, parameters = connection.execute.call_args.args
    assert parameters == (pair.manufacturer, pair.part_number, 456, 123, 7)
    assert pair.manufacturer not in sql and pair.part_number not in sql
    assert result.manufacturer == pair.manufacturer and result.part_number == pair.part_number


def test_removal_is_exact_scoped_and_does_not_delete_parent_or_catalog(settings, actor, transaction):
    connection, _, _, _, configure = transaction
    configure("remove")
    assert invoke("remove", settings, actor).deleted is True
    sql, parameters = connection.execute.call_args.args
    assert sql.startswith("DELETE FROM public.service_parts AS p ")
    assert parameters == (789, 456, 123, 7)
    assert "p.id = %s AND p.service_record_id = %s" in sql
    assert "RETURNING p.id, p.service_record_id" in sql
    assert all(not call.args[0].startswith("UPDATE") for call in connection.execute.call_args_list)


def test_missing_or_wrong_parent_snapshot_is_one_not_found(settings, actor, transaction):
    connection, events, _, _, _ = transaction
    connection.execute.return_value.fetchone.side_effect = [(123,), (456, 123), None]
    with pytest.raises(queries.ServicePartNotFoundError, match="Part snapshot not found"):
        invoke("remove", settings, actor)
    assert events[-2:] == ["rollback", "close"]


def test_unconfirmed_removal_is_rejected_before_connect(settings, actor, transaction):
    _, _, _, connector, _ = transaction
    with pytest.raises(ValueError, match="Confirm removal"):
        queries.remove_service_part(settings, actor=actor, vehicle_id=123, service_id=456, snapshot_id=789,
                                    confirmation=ServicePartRemovalRequest.model_construct(confirm_removal=False))
    connector.assert_not_called()


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("stage", ["query", "prepare", "commit", "close"])
@pytest.mark.parametrize("error_type", [psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled])
def test_availability_translation_happens_after_cleanup_without_retry(settings, actor, transaction, operation, stage, error_type):
    connection, events, failures, connector, configure = transaction
    configure(operation)
    error = error_type("Synthetic driver-private failure")
    if stage == "query":
        connection.execute.side_effect = error
    elif stage in ("commit", "close"):
        failures[stage] = error
    def prepare(result):
        if stage == "prepare":
            raise error
    with pytest.raises(queries.ServicePartsUnavailableError) as caught:
        invoke(operation, settings, actor, prepare_response=prepare)
    assert str(caught.value) == "Service parts unavailable. Please try again."
    assert events[-1] == "close" and connector.call_count == 1
    if stage in ("query", "prepare", "commit"):
        assert "rollback" in events


@pytest.mark.parametrize("operation", OPERATIONS)
def test_unexpected_preparation_failures_rollback_close_and_propagate(settings, actor, transaction, operation):
    _, events, _, _, configure = transaction
    configure(operation)
    def prepare(result):
        raise RuntimeError("Synthetic preparation failure")
    with pytest.raises(RuntimeError, match="preparation failure"):
        invoke(operation, settings, actor, prepare_response=prepare)
    assert events[-2:] == ["rollback", "close"]


@pytest.mark.parametrize("operation", ["list", "manual", "catalog", "remove"])
def test_wrong_parent_results_cannot_commit(settings, actor, transaction, operation):
    connection, events, _, _, configure = transaction
    configure(operation)
    if operation == "list":
        connection.execute.return_value.fetchall.return_value = [(789, 999, *SNAPSHOT[2:])]
    else:
        rows = [(123,), (456, 123)] + ([CATALOG] if operation == "catalog" else [])
        rows.append((789, 999) if operation == "remove" else (789, 999, *SNAPSHOT[2:]))
        connection.execute.return_value.fetchone.side_effect = rows
    with pytest.raises(RuntimeError, match="match"):
        invoke(operation, settings, actor)
    assert events[-2:] == ["rollback", "close"]


def test_invalid_public_result_rolls_back_before_preparation(settings, actor, transaction):
    connection, events, _, _, _ = transaction
    connection.execute.return_value.fetchone.side_effect = [(123,), (456, 123), (*SNAPSHOT[:6], 0, None)]
    prepare = Mock()
    with pytest.raises(ValidationError):
        invoke("manual", settings, actor, prepare_response=prepare)
    prepare.assert_not_called()
    assert events[-2:] == ["rollback", "close"]
