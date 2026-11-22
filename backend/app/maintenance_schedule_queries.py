from collections.abc import Callable

import psycopg

from app import database
from app.config import Settings
from app.maintenance_schedule_schemas import (
    DUPLICATE_NAME_DETAIL, EDITABLE_FIELDS, DuplicateScheduleNameResponse,
    MaintenanceSchedule, MaintenanceScheduleCreate, MaintenanceScheduleListResponse,
    MaintenanceSchedulePatch,
)
from app.session_queries import AuthenticatedSession
from app.vehicle_queries import VehicleNotFoundError


PUBLIC_FIELDS = ("id", "vehicle_id", *EDITABLE_FIELDS, "created_at")
_COLUMNS = ", ".join(PUBLIC_FIELDS)
_SCOPED_COLUMNS = ", ".join(f"m.{field}" for field in PUBLIC_FIELDS)
_WRITE_COLUMNS = ", ".join(EDITABLE_FIELDS)
_WRITE_VALUES = ", ".join("%s" for _ in EDITABLE_FIELDS)
_ASSIGNMENTS = ", ".join(f"{field} = %s" for field in EDITABLE_FIELDS)
_DATABASE_FAILURES = (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled)


class MaintenanceScheduleUnavailableError(RuntimeError):
    def __init__(self):
        super().__init__("Maintenance schedules unavailable. Please try again.")


class MaintenanceScheduleNotFoundError(RuntimeError):
    def __init__(self):
        super().__init__("Maintenance schedule not found.")


class DuplicateScheduleNameError(RuntimeError):
    def __init__(self, matches: list[MaintenanceSchedule]):
        super().__init__(DUPLICATE_NAME_DETAIL)
        self.response = DuplicateScheduleNameResponse(matches=matches)


def _require_owned_vehicle(connection, vehicle_id, owner_id, *, lock=False):
    row = connection.execute(
        "SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s"
        + (" FOR UPDATE" if lock else ""),
        (vehicle_id, owner_id),
    ).fetchone()
    if row is None:
        raise VehicleNotFoundError()


def _public_schedule(row):
    return MaintenanceSchedule.model_validate(dict(zip(PUBLIC_FIELDS, row, strict=True)))


def _owned_schedules(connection, vehicle_id, owner_id):
    rows = connection.execute(
        f"SELECT {_SCOPED_COLUMNS} FROM public.maintenance_schedules AS m "
        "JOIN public.vehicles AS v ON v.id = m.vehicle_id "
        "WHERE m.vehicle_id = %s AND v.user_id = %s ORDER BY m.id",
        (vehicle_id, owner_id),
    ).fetchall()
    return [_public_schedule(row) for row in rows]


def _require_duplicate_review(name, schedules, reviewed_ids, *, edited_id=None):
    normalized = name.strip().casefold()
    matches = [
        schedule for schedule in schedules
        if schedule.id != edited_id and schedule.name.strip().casefold() == normalized
    ]
    if {schedule.id for schedule in matches} != set(reviewed_ids or ()):
        raise DuplicateScheduleNameError(matches)


def _prepare(result, prepare_response):
    result.model_dump(mode="json")
    if prepare_response is not None:
        prepare_response(result)


def list_maintenance_schedules(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int,
    prepare_response: Callable[[MaintenanceScheduleListResponse], None] | None = None,
) -> MaintenanceScheduleListResponse:
    owner_id = actor.user.id
    try:
        with database.connect_database(settings, read_only=True) as connection:
            _require_owned_vehicle(connection, vehicle_id, owner_id)
            result = MaintenanceScheduleListResponse(
                vehicle_id=vehicle_id, schedules=_owned_schedules(connection, vehicle_id, owner_id),
            )
            _prepare(result, prepare_response)
    except _DATABASE_FAILURES:
        raise MaintenanceScheduleUnavailableError() from None
    return result


def create_maintenance_schedule(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int,
    schedule: MaintenanceScheduleCreate,
    prepare_response: Callable[[MaintenanceSchedule], None] | None = None,
) -> MaintenanceSchedule:
    owner_id = actor.user.id
    try:
        with database.connect_database(settings, read_only=False) as connection:
            _require_owned_vehicle(connection, vehicle_id, owner_id, lock=True)
            # A separate statement gets a fresh snapshot after the lock wait.
            schedules = _owned_schedules(connection, vehicle_id, owner_id)
            _require_duplicate_review(schedule.name, schedules, schedule.reviewed_duplicate_ids)
            row = connection.execute(
                f"INSERT INTO public.maintenance_schedules (vehicle_id, {_WRITE_COLUMNS}) "
                f"SELECT v.id, {_WRITE_VALUES} FROM public.vehicles AS v "
                f"WHERE v.id = %s AND v.user_id = %s RETURNING {_COLUMNS}",
                (*(getattr(schedule, field) for field in EDITABLE_FIELDS), vehicle_id, owner_id),
            ).fetchone()
            if row is None:
                raise VehicleNotFoundError()
            result = _public_schedule(row)
            if result.vehicle_id != vehicle_id:
                raise RuntimeError("Schedule result did not match the owned vehicle")
            _prepare(result, prepare_response)
    except _DATABASE_FAILURES:
        # A lost commit acknowledgment can leave a saved schedule. Never retry it here.
        raise MaintenanceScheduleUnavailableError() from None
    return result


def update_maintenance_schedule(
    settings: Settings, *, actor: AuthenticatedSession, vehicle_id: int, schedule_id: int,
    patch: MaintenanceSchedulePatch,
    prepare_response: Callable[[MaintenanceSchedule], None] | None = None,
) -> MaintenanceSchedule:
    owner_id = actor.user.id
    try:
        with database.connect_database(settings, read_only=False) as connection:
            _require_owned_vehicle(connection, vehicle_id, owner_id, lock=True)
            schedules = _owned_schedules(connection, vehicle_id, owner_id)
            current = next((schedule for schedule in schedules if schedule.id == schedule_id), None)
            if current is None:
                raise MaintenanceScheduleNotFoundError()
            values = patch.merged_values(current)
            _require_duplicate_review(
                values["name"], schedules, patch.reviewed_duplicate_ids, edited_id=schedule_id,
            )
            row = connection.execute(
                f"UPDATE public.maintenance_schedules AS m SET {_ASSIGNMENTS} "
                "FROM public.vehicles AS v WHERE m.id = %s AND m.vehicle_id = %s "
                f"AND v.id = m.vehicle_id AND v.user_id = %s RETURNING {_SCOPED_COLUMNS}",
                (*(values[field] for field in EDITABLE_FIELDS), schedule_id, vehicle_id, owner_id),
            ).fetchone()
            if row is None:
                raise MaintenanceScheduleNotFoundError()
            result = _public_schedule(row)
            if (result.id, result.vehicle_id) != (schedule_id, vehicle_id):
                raise RuntimeError("Updated schedule did not match the owned record")
            _prepare(result, prepare_response)
    except _DATABASE_FAILURES:
        raise MaintenanceScheduleUnavailableError() from None
    return result
