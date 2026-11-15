from collections.abc import Callable

import psycopg

from app import database
from app.config import Settings
from app.session_queries import AuthenticatedSession
from app.vehicle_schemas import (
    EDITABLE_FIELDS, Vehicle, VehicleCreate, VehicleListResponse, VehiclePatch,
    require_reading_confirmation,
)


PUBLIC_FIELDS = (
    "id", "year", "make", "model", "engine", "vehicle_type", "mileage",
    "operating_hours", "readings_updated_at", "created_at",
)
_PUBLIC_COLUMNS = ", ".join(PUBLIC_FIELDS)


class VehicleUnavailableError(RuntimeError):
    def __init__(self):
        super().__init__("Vehicles unavailable. Please try again.")


class VehicleNotFoundError(RuntimeError):
    def __init__(self):
        super().__init__("Vehicle not found.")


def _public_vehicle(row) -> Vehicle:
    if row is None:
        raise RuntimeError("Vehicle insertion returned no public record")
    return Vehicle.model_validate(dict(zip(PUBLIC_FIELDS, row, strict=True)))


def list_vehicles(
    settings: Settings, *, actor: AuthenticatedSession,
    prepare_response: Callable[[VehicleListResponse], None] | None = None,
) -> VehicleListResponse:
    try:
        with database.connect_database(settings, read_only=True) as connection:
            rows = connection.execute(
                f"SELECT {_PUBLIC_COLUMNS} FROM public.vehicles "
                "WHERE user_id = %s ORDER BY created_at DESC, id DESC",
                (actor.user.id,),
            ).fetchall()
            result = VehicleListResponse(vehicles=[_public_vehicle(row) for row in rows])
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        raise VehicleUnavailableError() from None
    return result


def create_vehicle(
    settings: Settings, *, actor: AuthenticatedSession, vehicle: VehicleCreate,
    prepare_response: Callable[[Vehicle], None] | None = None,
) -> Vehicle:
    try:
        with database.connect_database(settings, read_only=False) as connection:
            row = connection.execute(
                "INSERT INTO public.vehicles "
                "(user_id, year, make, model, engine, vehicle_type, mileage, "
                "operating_hours, readings_updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, "
                "CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END) "
                f"RETURNING {_PUBLIC_COLUMNS}",
                (actor.user.id, vehicle.year, vehicle.make, vehicle.model, vehicle.engine,
                 vehicle.vehicle_type, vehicle.mileage, vehicle.operating_hours,
                 vehicle.mileage is not None or vehicle.operating_hours is not None),
            ).fetchone()
            result = _public_vehicle(row)
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        # Context exit attempts rollback and closes before this translation.
        # A lost commit acknowledgment can still leave a committed vehicle.
        raise VehicleUnavailableError() from None
    return result


def get_vehicle(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int,
    prepare_response: Callable[[Vehicle], None] | None = None,
) -> Vehicle:
    try:
        with database.connect_database(settings, read_only=True) as connection:
            row = connection.execute(
                f"SELECT {_PUBLIC_COLUMNS} FROM public.vehicles "
                "WHERE id = %s AND user_id = %s", (vehicle_id, actor.user.id),
            ).fetchone()
            if row is None:
                raise VehicleNotFoundError()
            result = _public_vehicle(row)
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        raise VehicleUnavailableError() from None
    return result


def update_vehicle(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, patch: VehiclePatch,
    prepare_response: Callable[[Vehicle], None] | None = None,
) -> Vehicle:
    try:
        with database.connect_database(settings, read_only=False) as connection:
            row = connection.execute(
                f"SELECT {_PUBLIC_COLUMNS} FROM public.vehicles "
                "WHERE id = %s AND user_id = %s FOR UPDATE", (vehicle_id, actor.user.id),
            ).fetchone()
            if row is None:
                raise VehicleNotFoundError()
            current = _public_vehicle(row)
            stored = dict(zip(PUBLIC_FIELDS, row, strict=True))
            # The row is locked: no pre-lock snapshot may authorize a correction.
            require_reading_confirmation(current, patch)
            changes = patch.changes()
            merged = {name: changes.get(name, stored[name]) for name in EDITABLE_FIELDS}
            if any(value != stored[name] for name, value in merged.items()):
                readings_changed = (
                    merged["mileage"] != current.mileage
                    or merged["operating_hours"] != current.operating_hours
                )
                row = connection.execute(
                    "UPDATE public.vehicles SET year = %s, make = %s, model = %s, engine = %s, "
                    "vehicle_type = %s, mileage = %s, operating_hours = %s, "
                    "readings_updated_at = CASE WHEN %s THEN clock_timestamp() "
                    "ELSE readings_updated_at END "
                    f"WHERE id = %s AND user_id = %s RETURNING {_PUBLIC_COLUMNS}",
                    (merged["year"], merged["make"], merged["model"], merged["engine"],
                     merged["vehicle_type"], merged["mileage"], merged["operating_hours"],
                     readings_changed, vehicle_id, actor.user.id),
                ).fetchone()
                result = _public_vehicle(row)
            else:
                result = current
            result.model_dump(mode="json")
            if prepare_response is not None:
                prepare_response(result)
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        # Context exit attempts rollback and closes before translation. A lost
        # commit acknowledgment can still mean the update committed; never retry.
        raise VehicleUnavailableError() from None
    return result
