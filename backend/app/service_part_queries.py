from collections.abc import Callable

import psycopg

from app import database
from app.config import Settings
from app.service_part_schemas import (
    PART_REMOVAL_ERROR, CatalogPartLookup, CatalogPartPreview, CatalogServicePartCreate,
    ManualServicePartCreate, ServicePartListResponse, ServicePartRemovalRequest,
    ServicePartRemovalResponse, ServicePartSnapshot,
)
from app.service_queries import ServiceNotFoundError
from app.session_queries import AuthenticatedSession
from app.vehicle_queries import VehicleNotFoundError


PUBLIC_FIELDS = (
    "id", "service_record_id", "part_id", "name", "part_number", "manufacturer", "quantity", "notes",
)
CATALOG_FIELDS = ("id", "manufacturer", "part_number", "name", "category")
_PUBLIC_COLUMNS = ", ".join(PUBLIC_FIELDS)
_SELECT_COLUMNS = ", ".join(f"p.{field}" for field in PUBLIC_FIELDS)
_CATALOG_COLUMNS = ", ".join(f"p.{field}" for field in CATALOG_FIELDS)


class ServicePartsUnavailableError(RuntimeError):
    def __init__(self):
        super().__init__("Service parts unavailable. Please try again.")


class ServicePartNotFoundError(RuntimeError):
    def __init__(self):
        super().__init__("Part snapshot not found.")


class CatalogPartNotFoundError(RuntimeError):
    def __init__(self):
        super().__init__("Catalog part not found. Look it up again or enter the part manually.")


class CatalogPreviewConflictError(RuntimeError):
    def __init__(self):
        super().__init__("Catalog part changed or is no longer available. Look it up again or enter the part manually.")


def _require_owned_service(connection, actor, vehicle_id, service_id, *, lock=False):
    vehicle = connection.execute(
        "SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s",
        (vehicle_id, actor.user.id),
    ).fetchone()
    if vehicle is None:
        raise VehicleNotFoundError()
    service = connection.execute(
        "SELECT s.id, s.vehicle_id FROM public.service_records AS s "
        "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
        "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s"
        + (" FOR UPDATE OF s" if lock else ""),
        (service_id, vehicle_id, actor.user.id),
    ).fetchone()
    if service is None:
        raise ServiceNotFoundError()
    if service != (service_id, vehicle_id):
        raise RuntimeError("Service result did not match the owned parent")


def _catalog_row(connection, actor, vehicle_id, service_id, manufacturer, part_number, *, lock=False):
    return connection.execute(
        f"SELECT {_CATALOG_COLUMNS} FROM public.parts AS p "
        "CROSS JOIN public.service_records AS s JOIN public.vehicles AS v ON v.id = s.vehicle_id "
        "WHERE p.manufacturer = %s AND p.part_number = %s "
        "AND s.id = %s AND s.vehicle_id = %s AND v.user_id = %s"
        + (" FOR SHARE OF p" if lock else ""),
        (manufacturer, part_number, service_id, vehicle_id, actor.user.id),
    ).fetchone()


def _preview(row):
    return CatalogPartPreview.model_validate(dict(zip(CATALOG_FIELDS, row, strict=True)))


def _snapshot(row, service_id):
    result = ServicePartSnapshot.model_validate(dict(zip(PUBLIC_FIELDS, row, strict=True)))
    if result.service_record_id != service_id:
        raise RuntimeError("Part snapshot did not match the owned service")
    return result


def list_service_parts(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, service_id: int,
    prepare_response: Callable[[ServicePartListResponse], None] | None = None,
) -> ServicePartListResponse:
    try:
        with database.connect_database(settings, read_only=True) as connection:
            _require_owned_service(connection, actor, vehicle_id, service_id)
            rows = connection.execute(
                f"SELECT {_SELECT_COLUMNS} FROM public.service_parts AS p "
                "JOIN public.service_records AS s ON s.id = p.service_record_id "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s ORDER BY p.id ASC",
                (service_id, vehicle_id, actor.user.id),
            ).fetchall()
            result = ServicePartListResponse(vehicle_id=vehicle_id, service_record_id=service_id,
                                             parts=[_snapshot(row, service_id) for row in rows])
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        raise ServicePartsUnavailableError() from None
    return result


def lookup_catalog_part(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, service_id: int,
    lookup: CatalogPartLookup, prepare_response: Callable[[CatalogPartPreview], None] | None = None,
) -> CatalogPartPreview:
    try:
        with database.connect_database(settings, read_only=True) as connection:
            _require_owned_service(connection, actor, vehicle_id, service_id)
            row = _catalog_row(connection, actor, vehicle_id, service_id,
                               lookup.manufacturer, lookup.part_number)
            if row is None:
                raise CatalogPartNotFoundError()
            result = _preview(row)
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        raise ServicePartsUnavailableError() from None
    return result


def attach_service_part(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, service_id: int,
    part: ManualServicePartCreate | CatalogServicePartCreate,
    prepare_response: Callable[[ServicePartSnapshot], None] | None = None,
) -> ServicePartSnapshot:
    try:
        with database.connect_database(settings, read_only=False) as connection:
            _require_owned_service(connection, actor, vehicle_id, service_id, lock=True)
            if isinstance(part, CatalogServicePartCreate):
                row = _catalog_row(connection, actor, vehicle_id, service_id,
                                   part.preview.manufacturer, part.preview.part_number, lock=True)
                if row is None or _preview(row) != part.preview:
                    raise CatalogPreviewConflictError()
                # All snapshot identity bindings come from the locked server row.
                part_id, manufacturer, part_number, name, _category = row
            elif isinstance(part, ManualServicePartCreate):
                part_id, manufacturer, part_number, name = None, part.manufacturer, part.part_number, part.name
            else:
                raise TypeError("A validated manual or catalog snapshot is required")
            row = connection.execute(
                "INSERT INTO public.service_parts "
                "(service_record_id, part_id, name, part_number, manufacturer, quantity, notes) "
                "SELECT s.id, %s, %s, %s, %s, %s, %s FROM public.service_records AS s "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s "
                f"RETURNING {_PUBLIC_COLUMNS}",
                (part_id, name, part_number, manufacturer, part.quantity, part.notes,
                 service_id, vehicle_id, actor.user.id),
            ).fetchone()
            if row is None:
                raise ServiceNotFoundError()
            result = _snapshot(row, service_id)
            if result.part_id != part_id:
                raise RuntimeError("Part reference did not match the inserted snapshot")
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        # Context exit rolls back/closes before translation. A lost commit
        # acknowledgment can still mean the snapshot exists; never retry here.
        raise ServicePartsUnavailableError() from None
    return result


def remove_service_part(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, service_id: int,
    snapshot_id: int, confirmation: ServicePartRemovalRequest,
    prepare_response: Callable[[ServicePartRemovalResponse], None] | None = None,
) -> ServicePartRemovalResponse:
    if confirmation.confirm_removal is not True:
        raise ValueError(PART_REMOVAL_ERROR)
    try:
        with database.connect_database(settings, read_only=False) as connection:
            _require_owned_service(connection, actor, vehicle_id, service_id, lock=True)
            row = connection.execute(
                "DELETE FROM public.service_parts AS p USING public.service_records AS s, public.vehicles AS v "
                "WHERE p.id = %s AND p.service_record_id = %s AND s.id = p.service_record_id "
                "AND s.vehicle_id = %s AND v.id = s.vehicle_id AND v.user_id = %s "
                "RETURNING p.id, p.service_record_id",
                (snapshot_id, service_id, vehicle_id, actor.user.id),
            ).fetchone()
            if row is None:
                raise ServicePartNotFoundError()
            if row != (snapshot_id, service_id):
                raise RuntimeError("Removed snapshot did not match the owned record")
            result = ServicePartRemovalResponse(id=row[0], service_record_id=row[1], deleted=True)
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        raise ServicePartsUnavailableError() from None
    return result
