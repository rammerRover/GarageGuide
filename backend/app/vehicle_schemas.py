import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


MAX_READING = Decimal("99999999999.9")
READING_ERROR = "Enter a nonnegative decimal string with at most one decimal place, up to 99999999999.9."
UNICODE_ERROR = "Enter valid Unicode characters without NUL."
TEXT_ERROR = "Enter nonblank text."
VEHICLE_ID_ERROR = "Enter a vehicle ID from 1 through 2147483647 using digits without leading zeroes."
EMPTY_PATCH_ERROR = "Provide at least one editable vehicle field."
REQUIRED_PATCH_ERROR = "This field cannot be cleared."
CONFIRMATION_ERROR = "Provide confirmation values only for supplied reading fields."
EDITABLE_FIELDS = ("year", "make", "model", "vehicle_type", "engine", "mileage", "operating_hours")
_READING_FIELDS = ("mileage", "operating_hours")


def get_current_year() -> int:
    return date.today().year


def validate_vehicle_id(value: object) -> int:
    # Validate decoded path text before coercion can erase a forbidden spelling.
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]{0,9}", value) is None:
        raise ValueError(VEHICLE_ID_ERROR)
    number = int(value)
    if number > 2147483647:
        raise ValueError(VEHICLE_ID_ERROR)
    return number


def _validate_year(value: int) -> int:
    maximum = get_current_year() + 1
    if not 1886 <= value <= maximum:
        raise ValueError(f"Enter a model year from 1886 through {maximum}.")
    return value


def _trim_safe_text(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError(UNICODE_ERROR) from None
    if "\x00" in value:
        raise ValueError(UNICODE_ERROR)
    return value.strip()


def _nonblank(value: str) -> str:
    if not value:
        raise ValueError(TEXT_ERROR)
    return value


def _optional_text(value: object) -> object:
    value = _trim_safe_text(value)
    return None if value == "" else value


def _parse_reading(value: object) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9])?", value.strip()):
        raise ValueError(READING_ERROR)
    number = Decimal(value.strip())
    if number > MAX_READING:
        raise ValueError(READING_ERROR)
    return number


def _stored_reading(value: object) -> Decimal:
    if not isinstance(value, Decimal):
        return _parse_reading(value)
    if (
        not value.is_finite() or value < 0 or value > MAX_READING
        or value % Decimal("0.1") != 0
    ):
        raise ValueError(READING_ERROR)
    return value.copy_abs() if value == 0 else value


VehicleText = Annotated[str, BeforeValidator(_trim_safe_text), AfterValidator(_nonblank)]
OptionalEngine = Annotated[str | None, BeforeValidator(_optional_text)]
RequestReading = Annotated[Decimal, BeforeValidator(_parse_reading, json_schema_input_type=str)]
StoredReading = Annotated[Decimal, BeforeValidator(_stored_reading)]
VehicleId = Annotated[int, BeforeValidator(validate_vehicle_id, json_schema_input_type=str)]


class VehicleCreate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    year: int
    make: VehicleText
    model: VehicleText
    vehicle_type: VehicleText
    engine: OptionalEngine = None
    mileage: RequestReading | None = None
    operating_hours: RequestReading | None = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        return _validate_year(value)

    @field_serializer("mileage", "operating_hours")
    def serialize_reading(self, value: Decimal | None) -> str | None:
        return format(value, ".1f") if value is not None else None


class ReadingConfirmation(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    mileage: RequestReading | None = None
    operating_hours: RequestReading | None = None

    @field_validator("mileage", "operating_hours", mode="before", json_schema_input_type=str)
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError(CONFIRMATION_ERROR)
        return value

    @field_serializer("mileage", "operating_hours")
    def serialize_reading(self, value: Decimal | None) -> str | None:
        return format(value, ".1f") if value is not None else None


class VehiclePatch(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    year: int | None = None
    make: VehicleText | None = None
    model: VehicleText | None = None
    vehicle_type: VehicleText | None = None
    engine: OptionalEngine = None
    mileage: RequestReading | None = None
    operating_hours: RequestReading | None = None
    reading_confirmation: ReadingConfirmation | None = None

    @field_validator("year", mode="before", json_schema_input_type=int)
    @classmethod
    def require_year_value(cls, value: object) -> object:
        if value is None:
            raise ValueError(REQUIRED_PATCH_ERROR)
        return value

    @field_validator("make", "model", "vehicle_type", mode="before", json_schema_input_type=str)
    @classmethod
    def require_text_value(cls, value: object) -> object:
        if value is None:
            raise ValueError(REQUIRED_PATCH_ERROR)
        return value

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        return _validate_year(value)

    @field_validator("reading_confirmation", mode="before", json_schema_input_type=ReadingConfirmation)
    @classmethod
    def require_confirmation_object(cls, value: object) -> object:
        if not isinstance(value, dict):
            raise ValueError(CONFIRMATION_ERROR)
        return value

    @model_validator(mode="after")
    def validate_supplied_fields(self) -> Self:
        if not self.model_fields_set.intersection(EDITABLE_FIELDS):
            raise ValueError(EMPTY_PATCH_ERROR)
        if self.reading_confirmation is not None:
            if not self.reading_confirmation.model_fields_set.issubset(self.model_fields_set):
                raise ValueError(CONFIRMATION_ERROR)
        return self

    @field_serializer("mileage", "operating_hours")
    def serialize_reading(self, value: Decimal | None) -> str | None:
        return format(value, ".1f") if value is not None else None

    def changes(self) -> dict[str, object]:
        """Return only supplied business values, retaining Decimal/null bindings."""
        return {name: getattr(self, name) for name in EDITABLE_FIELDS if name in self.model_fields_set}


class Vehicle(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    id: int = Field(gt=0)
    year: int = Field(ge=1, le=32767)
    make: VehicleText
    model: VehicleText
    engine: OptionalEngine
    vehicle_type: VehicleText
    mileage: StoredReading | None
    operating_hours: StoredReading | None
    readings_updated_at: AwareDatetime | None
    created_at: AwareDatetime

    @field_serializer("mileage", "operating_hours")
    def serialize_reading(self, value: Decimal | None) -> str | None:
        return format(value, ".1f") if value is not None else None


class VehicleListResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    vehicles: list[Vehicle]


class ReadingConfirmationRequired(ValueError):
    def __init__(self, fields: tuple[str, ...], current_readings: dict[str, str]):
        super().__init__("Reading changes require confirmation.")
        self.fields = fields
        self.current_readings = current_readings.copy()


def require_reading_confirmation(current: Vehicle, patch: VehiclePatch) -> None:
    """Compare only; the writable query must supply its freshly locked row."""
    changes = patch.changes()
    acknowledgments = (
        {} if patch.reading_confirmation is None else {
            name: getattr(patch.reading_confirmation, name)
            for name in patch.reading_confirmation.model_fields_set
        }
    )
    required = tuple(
        name for name in _READING_FIELDS if name in changes
        and getattr(current, name) is not None
        and (changes[name] is None or changes[name] < getattr(current, name))
    )
    stale = any(value != getattr(current, name) for name, value in acknowledgments.items())
    if stale or any(name not in acknowledgments for name in required):
        raise ReadingConfirmationRequired(
            required, {name: format(getattr(current, name), ".1f") for name in required},
        )
