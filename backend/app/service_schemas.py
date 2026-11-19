import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator, AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field,
    field_serializer, field_validator, model_validator,
)

from app.vehicle_schemas import (
    RequestReading, StoredReading, VehicleText, _optional_text, validate_vehicle_id,
)


SERVICE_ID_ERROR = "Enter a service ID from 1 through 2147483647 using digits without leading zeroes."
SERVICE_DATE_ERROR = "Enter a valid service date on or before today using YYYY-MM-DD."
COST_ERROR = "Enter a nonnegative decimal string with at most two decimal places, up to 9999999999.99."
EMPTY_PATCH_ERROR = "Provide at least one editable service field."
REQUIRED_PATCH_ERROR = "This field cannot be cleared."
REMOVAL_ERROR = "Confirm removal with true."
MAX_COST = Decimal("9999999999.99")
EDITABLE_FIELDS = (
    "service_date", "service_type", "description", "mileage", "operating_hours", "cost", "notes",
)


def get_current_date() -> date:
    return date.today()


def validate_service_id(value: object) -> int:
    try:
        return validate_vehicle_id(value)
    except ValueError:
        raise ValueError(SERVICE_ID_ERROR) from None


def _parse_service_date(value: object) -> date:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ValueError(SERVICE_DATE_ERROR)
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(SERVICE_DATE_ERROR) from None


def _not_future(value: date) -> date:
    if value > get_current_date():
        raise ValueError(SERVICE_DATE_ERROR)
    return value


def _parse_cost(value: object) -> Decimal:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", value.strip()) is None:
        raise ValueError(COST_ERROR)
    number = Decimal(value.strip())
    if number > MAX_COST:
        raise ValueError(COST_ERROR)
    return number


def _stored_cost(value: object) -> Decimal:
    if not isinstance(value, Decimal):
        return _parse_cost(value)
    if (
        not value.is_finite() or value < 0 or value > MAX_COST
        or value % Decimal("0.01") != 0
    ):
        raise ValueError(COST_ERROR)
    return value.copy_abs() if value == 0 else value


ServiceId = Annotated[int, BeforeValidator(validate_service_id, json_schema_input_type=str)]
RequestDate = Annotated[
    date, BeforeValidator(_parse_service_date, json_schema_input_type=str), AfterValidator(_not_future),
]
ServiceType = Literal["maintenance", "repair", "inspection", "diagnostic"]
OptionalNotes = Annotated[str | None, BeforeValidator(_optional_text)]
RequestCost = Annotated[Decimal, BeforeValidator(_parse_cost, json_schema_input_type=str)]
StoredCost = Annotated[Decimal, BeforeValidator(_stored_cost)]


class _ServiceValues(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    @field_serializer("mileage", "operating_hours", check_fields=False)
    def serialize_reading(self, value: Decimal | None) -> str | None:
        return format(value, ".1f") if value is not None else None

    @field_serializer("cost", check_fields=False)
    def serialize_cost(self, value: Decimal | None) -> str | None:
        return format(value, ".2f") if value is not None else None


class ServiceCreate(_ServiceValues):
    service_date: RequestDate
    service_type: ServiceType
    description: VehicleText
    mileage: RequestReading | None = None
    operating_hours: RequestReading | None = None
    cost: RequestCost | None = None
    notes: OptionalNotes = None


class ServicePatch(_ServiceValues):
    service_date: RequestDate | None = None
    service_type: ServiceType | None = None
    description: VehicleText | None = None
    mileage: RequestReading | None = None
    operating_hours: RequestReading | None = None
    cost: RequestCost | None = None
    notes: OptionalNotes = None

    @field_validator("service_date", "service_type", "description", mode="before")
    @classmethod
    def require_value(cls, value: object) -> object:
        if value is None:
            raise ValueError(REQUIRED_PATCH_ERROR)
        return value

    @model_validator(mode="after")
    def require_business_field(self) -> Self:
        if not self.model_fields_set.intersection(EDITABLE_FIELDS):
            raise ValueError(EMPTY_PATCH_ERROR)
        return self

    def changes(self) -> dict[str, object]:
        """Return supplied fields with native date/Decimal/null bindings."""
        return {name: getattr(self, name) for name in EDITABLE_FIELDS if name in self.model_fields_set}


class ServiceRemovalRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    confirm_removal: bool

    @field_validator("confirm_removal")
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError(REMOVAL_ERROR)
        return value


class ServiceRecord(_ServiceValues):
    id: int = Field(gt=0, le=2147483647)
    vehicle_id: int = Field(gt=0, le=2147483647)
    service_date: date
    service_type: ServiceType
    description: VehicleText
    mileage: StoredReading | None
    operating_hours: StoredReading | None
    cost: StoredCost | None
    notes: OptionalNotes
    created_at: AwareDatetime


class ServiceListResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    vehicle_id: int = Field(gt=0, le=2147483647)
    services: list[ServiceRecord]

    @model_validator(mode="after")
    def require_matching_vehicle(self) -> Self:
        if any(service.vehicle_id != self.vehicle_id for service in self.services):
            raise ValueError("Service records must match the requested vehicle.")
        return self


class ServiceRemovalResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    id: int = Field(gt=0, le=2147483647)
    vehicle_id: int = Field(gt=0, le=2147483647)
    deleted: bool

    @field_validator("deleted")
    @classmethod
    def require_removed(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Removal response must confirm deletion.")
        return value
