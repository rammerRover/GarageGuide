from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator, AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field,
    ValidationError, field_serializer, field_validator, model_validator,
)
from pydantic_core import PydanticCustomError

from app.service_schemas import get_current_date
from app.vehicle_schemas import (
    TEXT_ERROR, RequestReading, StoredReading, VehicleText, _optional_text, validate_vehicle_id,
)


SCHEDULE_ID_ERROR = "Enter a schedule ID from 1 through 2147483647 using digits without leading zeroes."
BASELINE_DATE_ERROR = "Enter a valid baseline date on or before today using YYYY-MM-DD."
POSITIVE_INTERVAL_ERROR = "Enter an interval greater than zero."
EMPTY_PATCH_ERROR = "Provide at least one editable schedule field."
REVIEW_IDS_ERROR = "Provide distinct schedule IDs from the duplicate review."
AT_LEAST_ONE_PAIR_ERROR = "Enable at least one maintenance interval."
DUPLICATE_NAME_DETAIL = "Review the matching schedules before saving a separate task."

_PAIRS = (
    ("interval_days", "baseline_date", "day"),
    ("interval_miles", "baseline_mileage", "mileage"),
    ("interval_hours", "baseline_hours", "operating-hour"),
)
EDITABLE_FIELDS = (
    "name", "interval_days", "interval_miles", "interval_hours",
    "baseline_date", "baseline_mileage", "baseline_hours", "source_notes",
)


def validate_schedule_id(value: object) -> int:
    try:
        return validate_vehicle_id(value)
    except ValueError:
        raise ValueError(SCHEDULE_ID_ERROR) from None


def _parse_baseline_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError(BASELINE_DATE_ERROR)
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError(BASELINE_DATE_ERROR) from None
    if value != parsed.isoformat() or parsed > get_current_date():
        raise ValueError(BASELINE_DATE_ERROR)
    return parsed


def _positive_interval(value: Decimal) -> Decimal:
    if value <= 0:
        raise ValueError(POSITIVE_INTERVAL_ERROR)
    return value


def _validate_complete_values(values: dict[str, object]) -> None:
    # Validate after a PATCH is merged, since its missing counterpart may be stored.
    errors: list[tuple[str, str]] = []
    for interval, baseline, label in _PAIRS:
        if values[interval] is not None and values[baseline] is None:
            errors.append((baseline, f"Provide a baseline for the enabled {label} interval."))
        elif values[interval] is None and values[baseline] is not None:
            errors.append((baseline, f"Clear this baseline or enable its {label} interval."))
    if not errors and all(values[interval] is None for interval, _, _ in _PAIRS):
        errors.append(("interval_days", AT_LEAST_ONE_PAIR_ERROR))

    baseline_date = values["baseline_date"]
    if isinstance(baseline_date, date) and baseline_date > get_current_date():
        errors.append(("baseline_date", BASELINE_DATE_ERROR))
    name = values["name"]
    if isinstance(name, str) and not name.strip():
        errors.append(("name", TEXT_ERROR))
    if errors:
        raise ValidationError.from_exception_data(
            "MaintenanceSchedule",
            [
                {"type": PydanticCustomError("schedule_value", message), "loc": (field,), "input": None}
                for field, message in errors
            ],
        )


ScheduleId = Annotated[int, BeforeValidator(validate_schedule_id, json_schema_input_type=str)]
_PositiveInteger = Annotated[int, Field(gt=0, le=2147483647)]
_RequestDate = Annotated[date, BeforeValidator(_parse_baseline_date, json_schema_input_type=str)]
_RequestInterval = Annotated[RequestReading, AfterValidator(_positive_interval)]
_StoredInterval = Annotated[StoredReading, AfterValidator(_positive_interval)]
_OptionalNotes = Annotated[str | None, BeforeValidator(_optional_text)]


class _ScheduleModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    @field_serializer(
        "interval_miles", "interval_hours", "baseline_mileage", "baseline_hours",
        check_fields=False, when_used="json",
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        return format(value, ".1f") if value is not None else None


class _ScheduleWrite(_ScheduleModel):
    interval_days: _PositiveInteger | None = None
    interval_miles: _RequestInterval | None = None
    interval_hours: _RequestInterval | None = None
    baseline_date: _RequestDate | None = None
    baseline_mileage: RequestReading | None = None
    baseline_hours: RequestReading | None = None
    source_notes: _OptionalNotes = None
    reviewed_duplicate_ids: Annotated[list[_PositiveInteger], Field(min_length=1)] | None = None

    @field_validator("reviewed_duplicate_ids")
    @classmethod
    def validate_review_ids(cls, value: list[int] | None) -> list[int]:
        if value is None or len(value) != len(set(value)):
            raise ValueError(REVIEW_IDS_ERROR)
        return value


class MaintenanceScheduleCreate(_ScheduleWrite):
    name: VehicleText

    @model_validator(mode="after")
    def validate_schedule(self) -> Self:
        _validate_complete_values({field: getattr(self, field) for field in EDITABLE_FIELDS})
        return self


class MaintenanceSchedulePatch(_ScheduleWrite):
    name: VehicleText | None = None

    @field_validator("name")
    @classmethod
    def require_name_value(cls, value: str | None) -> str:
        if value is None:
            raise ValueError(TEXT_ERROR)
        return value

    @model_validator(mode="after")
    def require_edit(self) -> Self:
        if not self.model_fields_set.intersection(EDITABLE_FIELDS):
            raise ValueError(EMPTY_PATCH_ERROR)
        return self

    def merged_values(self, current: "MaintenanceSchedule") -> dict[str, object]:
        """Return validated native values from the current row and supplied edits."""
        values = {
            field: getattr(self if field in self.model_fields_set else current, field)
            for field in EDITABLE_FIELDS
        }
        _validate_complete_values(values)
        return values


class MaintenanceSchedule(_ScheduleModel):
    id: _PositiveInteger
    vehicle_id: _PositiveInteger
    # Read stored text and dates as-is. Write-time rules apply on creation or edit.
    name: str
    interval_days: _PositiveInteger | None
    interval_miles: _StoredInterval | None
    interval_hours: _StoredInterval | None
    baseline_date: date | None
    baseline_mileage: StoredReading | None
    baseline_hours: StoredReading | None
    source_notes: str | None
    created_at: AwareDatetime


class MaintenanceScheduleListResponse(_ScheduleModel):
    vehicle_id: _PositiveInteger
    schedules: list[MaintenanceSchedule]

    @model_validator(mode="after")
    def require_matching_vehicle(self) -> Self:
        if any(schedule.vehicle_id != self.vehicle_id for schedule in self.schedules):
            raise ValueError("Schedules must match the requested vehicle.")
        return self


class DuplicateScheduleNameResponse(_ScheduleModel):
    code: Literal["duplicate_schedule_name"] = "duplicate_schedule_name"
    detail: str = DUPLICATE_NAME_DETAIL
    matches: list[MaintenanceSchedule]
