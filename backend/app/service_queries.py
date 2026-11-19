from collections.abc import Callable

import psycopg

from app import database
from app.config import Settings
from app.service_schemas import (
    EDITABLE_FIELDS, REMOVAL_ERROR, ServiceCreate, ServiceListResponse, ServicePatch,
    ServiceRecord, ServiceRemovalRequest, ServiceRemovalResponse,
)
from app.session_queries import AuthenticatedSession
from app.vehicle_queries import VehicleNotFoundError


PUBLIC_FIELDS = (
    "id", "vehicle_id", "service_date", "service_type", "description", "mileage",
    "operating_hours", "cost", "notes", "created_at",
)
_PUBLIC_COLUMNS = ", ".join(PUBLIC_FIELDS)
_SELECT_COLUMNS = ", ".join(f"s.{field}" for field in PUBLIC_FIELDS)


class ServiceUnavailableError(RuntimeError):
    def __init__(self):
        super().__init__("Service history unavailable. Please try again.")


class ServiceNotFoundError(RuntimeError):
    def __init__(self):
        super().__init__("Service record not found.")


class ServiceEditBlockedError(RuntimeError):
    def __init__(self):
        super().__init__("Service record is linked to maintenance completion and cannot be changed.")


class ServiceRemovalBlockedError(RuntimeError):
    def __init__(self):
        super().__init__("Service record has linked data and cannot be removed.")


def _require_owned_vehicle(connection, vehicle_id: int, actor: AuthenticatedSession) -> None:
    row = connection.execute(
        "SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s",
        (vehicle_id, actor.user.id),
    ).fetchone()
    if row is None:
        raise VehicleNotFoundError()


def _public_service(row) -> ServiceRecord:
    if row is None:
        raise RuntimeError("Service insertion returned no public record")
    return ServiceRecord.model_validate(dict(zip(PUBLIC_FIELDS, row, strict=True)))


def list_services(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int,
    prepare_response: Callable[[ServiceListResponse], None] | None = None,
) -> ServiceListResponse:
    try:
        with database.connect_database(settings, read_only=True) as connection:
            _require_owned_vehicle(connection, vehicle_id, actor)
            rows = connection.execute(
                f"SELECT {_SELECT_COLUMNS} FROM public.service_records AS s "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.vehicle_id = %s AND v.user_id = %s "
                "ORDER BY s.service_date DESC, s.created_at DESC, s.id DESC",
                (vehicle_id, actor.user.id),
            ).fetchall()
            result = ServiceListResponse(
                vehicle_id=vehicle_id, services=[_public_service(row) for row in rows],
            )
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        raise ServiceUnavailableError() from None
    return result


def create_service(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, service: ServiceCreate,
    prepare_response: Callable[[ServiceRecord], None] | None = None,
) -> ServiceRecord:
    try:
        with database.connect_database(settings, read_only=False) as connection:
            _require_owned_vehicle(connection, vehicle_id, actor)
            row = connection.execute(
                "INSERT INTO public.service_records "
                "(vehicle_id, service_date, service_type, description, mileage, operating_hours, cost, notes) "
                "SELECT v.id, %s, %s, %s, %s, %s, %s, %s "
                "FROM public.vehicles AS v WHERE v.id = %s AND v.user_id = %s "
                f"RETURNING {_PUBLIC_COLUMNS}",
                (service.service_date, service.service_type, service.description, service.mileage,
                 service.operating_hours, service.cost, service.notes, vehicle_id, actor.user.id),
            ).fetchone()
            if row is None:
                raise VehicleNotFoundError()
            result = _public_service(row)
            if result.vehicle_id != vehicle_id:
                raise RuntimeError("Service result did not match the owned vehicle")
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        # Context exit attempts rollback and closes before translation. A lost
        # acknowledgment can still mean the INSERT committed; never retry it.
        raise ServiceUnavailableError() from None
    return result


def _owned_service_row(connection, actor, vehicle_id, service_id, *, lock=False):
    row = connection.execute(
        f"SELECT {_SELECT_COLUMNS} FROM public.service_records AS s "
        "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
        "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s"
        + (" FOR UPDATE OF s" if lock else ""),
        (service_id, vehicle_id, actor.user.id),
    ).fetchone()
    if row is None:
        raise ServiceNotFoundError()
    if row[:2] != (service_id, vehicle_id):
        raise RuntimeError("Service result did not match the owned record")
    return row


def _linked_records(connection, actor, vehicle_id, service_id):
    row = connection.execute(
        "SELECT EXISTS (SELECT 1 FROM public.maintenance_completions AS c "
        "WHERE c.service_record_id = s.id AND c.vehicle_id = s.vehicle_id), "
        "EXISTS (SELECT 1 FROM public.service_parts AS p WHERE p.service_record_id = s.id) "
        "FROM public.service_records AS s JOIN public.vehicles AS v ON v.id = s.vehicle_id "
        "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
        (service_id, vehicle_id, actor.user.id),
    ).fetchone()
    if row is None:
        raise ServiceNotFoundError()
    if len(row) != 2 or any(type(value) is not bool for value in row):
        raise RuntimeError("Invalid service link state")
    return row


def get_service(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, service_id: int,
    prepare_response: Callable[[ServiceRecord], None] | None = None,
) -> ServiceRecord:
    try:
        with database.connect_database(settings, read_only=True) as connection:
            result = _public_service(_owned_service_row(connection, actor, vehicle_id, service_id))
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        raise ServiceUnavailableError() from None
    return result


def update_service(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, service_id: int,
    patch: ServicePatch, prepare_response: Callable[[ServiceRecord], None] | None = None,
) -> ServiceRecord:
    try:
        with database.connect_database(settings, read_only=False) as connection:
            row = _owned_service_row(connection, actor, vehicle_id, service_id, lock=True)
            current = _public_service(row)
            stored = dict(zip(PUBLIC_FIELDS, row, strict=True))
            changes = patch.changes()
            merged = {name: changes.get(name, stored[name]) for name in EDITABLE_FIELDS}
            if any(value != stored[name] for name, value in merged.items()):
                completion, _ = _linked_records(connection, actor, vehicle_id, service_id)
                if completion:
                    raise ServiceEditBlockedError()
                row = connection.execute(
                    "UPDATE public.service_records AS s SET service_date = %s, service_type = %s, "
                    "description = %s, mileage = %s, operating_hours = %s, cost = %s, notes = %s "
                    "FROM public.vehicles AS v WHERE s.id = %s AND s.vehicle_id = %s "
                    "AND v.id = s.vehicle_id AND v.user_id = %s "
                    f"RETURNING {_SELECT_COLUMNS}",
                    (*(merged[name] for name in EDITABLE_FIELDS), service_id, vehicle_id, actor.user.id),
                ).fetchone()
                if row is None:
                    raise ServiceNotFoundError()
                if row[:2] != (service_id, vehicle_id):
                    raise RuntimeError("Updated service did not match the owned record")
                result = _public_service(row)
            else:
                result = current
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        # Commit/close failures may leave a committed correction; never retry.
        raise ServiceUnavailableError() from None
    return result


def remove_service(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, service_id: int,
    confirmation: ServiceRemovalRequest,
    prepare_response: Callable[[ServiceRemovalResponse], None] | None = None,
) -> ServiceRemovalResponse:
    if confirmation.confirm_removal is not True:
        raise ValueError(REMOVAL_ERROR)
    try:
        with database.connect_database(settings, read_only=False) as connection:
            _public_service(_owned_service_row(connection, actor, vehicle_id, service_id, lock=True))
            if any(_linked_records(connection, actor, vehicle_id, service_id)):
                raise ServiceRemovalBlockedError()
            removed = connection.execute(
                "DELETE FROM public.service_records AS s USING public.vehicles AS v "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.id = s.vehicle_id AND v.user_id = %s "
                "RETURNING s.id, s.vehicle_id",
                (service_id, vehicle_id, actor.user.id),
            ).fetchone()
            if removed is None:
                raise ServiceNotFoundError()
            if removed != (service_id, vehicle_id):
                raise RuntimeError("Removed service did not match the owned record")
            result = ServiceRemovalResponse(id=removed[0], vehicle_id=removed[1], deleted=True)
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        # A lost removal acknowledgment cannot safely be replayed automatically.
        raise ServiceUnavailableError() from None
    return result
