from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from app.maintenance_schedule_schemas import MaintenanceSchedule
from app.vehicle_schemas import Vehicle


Status = Literal["upcoming", "due", "overdue", "needs_information"]
ReadingKind = Literal["mileage", "hours"]
LimitIssue = Literal["missing_reading", "below_baseline", "invalid_baseline"]
ReadingTimestampWarning = Literal["missing", "future", "at_least_30_days_old"]

_PRIORITY = {"upcoming": 0, "needs_information": 1, "due": 2, "overdue": 3}
_ADVISORY_AGE = timedelta(days=30)


class _StatusModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)


class _LimitStatus(_StatusModel):
    status: Status
    issue: LimitIssue | None


class DayLimitStatus(_LimitStatus):
    kind: Literal["days"] = "days"
    due_value: date | None
    remaining: int | None


class ReadingLimitStatus(_LimitStatus):
    kind: ReadingKind
    due_value: Decimal | None
    remaining: Decimal | None

    @field_serializer("due_value", "remaining", when_used="json")
    def serialize_amount(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return "0.0" if value == 0 else format(value, ".1f")


LimitStatus = Annotated[DayLimitStatus | ReadingLimitStatus, Field(discriminator="kind")]


class ScheduleMaintenanceStatus(_StatusModel):
    schedule: MaintenanceSchedule
    status: Status
    limits: list[LimitStatus]


class MaintenanceStatusResponse(_StatusModel):
    vehicle: Vehicle
    as_of_date: date
    readings_timestamp_warning: ReadingTimestampWarning | None
    schedules: list[ScheduleMaintenanceStatus]

    @model_validator(mode="after")
    def require_matching_vehicle(self) -> Self:
        if any(entry.schedule.vehicle_id != self.vehicle.id for entry in self.schedules):
            raise ValueError("Schedules must match the status vehicle.")
        return self


def _comparison(remaining: int | Decimal) -> Status:
    if remaining < 0:
        return "overdue"
    if remaining == 0:
        return "due"
    return "upcoming"


def _day_status(interval: int, baseline: date | None, today: date) -> DayLimitStatus:
    if baseline is None or baseline > today:
        return DayLimitStatus(status="needs_information", due_value=None, remaining=None, issue="invalid_baseline")

    # Ordinals preserve the exact target and remaining days beyond date.max.
    due_ordinal = baseline.toordinal() + interval
    remaining = due_ordinal - today.toordinal()
    due_date = date.fromordinal(due_ordinal) if due_ordinal <= date.max.toordinal() else None
    return DayLimitStatus(status=_comparison(remaining), due_value=due_date, remaining=remaining, issue=None)


def _reading_status(
    kind: ReadingKind, interval: Decimal, baseline: Decimal | None, current: Decimal | None,
) -> ReadingLimitStatus:
    if baseline is None:
        return ReadingLimitStatus(
            kind=kind, status="needs_information", due_value=None, remaining=None, issue="invalid_baseline",
        )

    target = baseline + interval
    if current is None or current < baseline:
        issue = "missing_reading" if current is None else "below_baseline"
        return ReadingLimitStatus(kind=kind, status="needs_information", due_value=target, remaining=None, issue=issue)

    remaining = target - current
    return ReadingLimitStatus(kind=kind, status=_comparison(remaining), due_value=target, remaining=remaining, issue=None)


def _schedule_status(schedule: MaintenanceSchedule, vehicle: Vehicle, today: date) -> ScheduleMaintenanceStatus:
    limits: list[LimitStatus] = []
    if schedule.interval_days is not None:
        limits.append(_day_status(schedule.interval_days, schedule.baseline_date, today))
    if schedule.interval_miles is not None:
        limits.append(_reading_status("mileage", schedule.interval_miles, schedule.baseline_mileage, vehicle.mileage))
    if schedule.interval_hours is not None:
        limits.append(_reading_status("hours", schedule.interval_hours, schedule.baseline_hours, vehicle.operating_hours))

    status = max((limit.status for limit in limits), key=_PRIORITY.__getitem__, default="upcoming")
    return ScheduleMaintenanceStatus(schedule=schedule, status=status, limits=limits)


def _timestamp_warning(updated_at: datetime | None, now_utc: datetime) -> ReadingTimestampWarning | None:
    if updated_at is None:
        return "missing"
    elapsed = now_utc - updated_at.astimezone(UTC)
    if elapsed < timedelta(0):
        return "future"
    if elapsed >= _ADVISORY_AGE:
        return "at_least_30_days_old"
    return None


def calculate_maintenance_status(
    vehicle: Vehicle,
    schedules: Iterable[MaintenanceSchedule],
    *,
    as_of_date: date,
    now: datetime,
) -> MaintenanceStatusResponse:
    """Evaluate the saved snapshot using the caller's captured date and clock instant."""
    if now.utcoffset() is None:
        raise ValueError("Maintenance status evaluation requires an aware clock instant.")
    warning = _timestamp_warning(vehicle.readings_updated_at, now.astimezone(UTC))
    # Adding two NUMERIC(12,1) readings can require 13 significant digits.
    with localcontext() as context:
        context.prec = 13
        entries = [
            _schedule_status(schedule, vehicle, as_of_date)
            for schedule in sorted(schedules, key=lambda schedule: schedule.id)
        ]
    return MaintenanceStatusResponse(
        vehicle=vehicle, as_of_date=as_of_date, readings_timestamp_warning=warning, schedules=entries,
    )
