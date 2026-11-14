import re
from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)


MAX_READING = Decimal("99999999999.9")
READING_ERROR = "Enter a nonnegative decimal string with at most one decimal place, up to 99999999999.9."
UNICODE_ERROR = "Enter valid Unicode characters without NUL."
TEXT_ERROR = "Enter nonblank text."


def get_current_year() -> int:
    return date.today().year


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
        maximum = get_current_year() + 1
        if not 1886 <= value <= maximum:
            raise ValueError(f"Enter a model year from 1886 through {maximum}.")
        return value

    @field_serializer("mileage", "operating_hours")
    def serialize_reading(self, value: Decimal | None) -> str | None:
        return format(value, ".1f") if value is not None else None


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
