from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator,
)

from app.vehicle_schemas import (
    TEXT_ERROR, VehicleText, _optional_text, _trim_safe_text, validate_vehicle_id,
)


SERVICE_PART_ID_ERROR = "Enter a part snapshot ID from 1 through 2147483647 using digits without leading zeroes."
PART_REMOVAL_ERROR = "Confirm removal with true."


def validate_service_part_id(value: object) -> int:
    try:
        return validate_vehicle_id(value)
    except ValueError:
        raise ValueError(SERVICE_PART_ID_ERROR) from None


def _exact_required_text(value: object) -> object:
    # Reuse Unicode/nonblank checks, preserving the original catalog spelling.
    if _trim_safe_text(value) == "":
        raise ValueError(TEXT_ERROR)
    return value


def _stored_optional_text(value: object) -> object:
    # Stored snapshots are historical: validate safety without rewriting text.
    _trim_safe_text(value)
    return value


ServicePartId = Annotated[int, BeforeValidator(validate_service_part_id, json_schema_input_type=str)]
PositiveInteger = Annotated[int, Field(strict=True, gt=0, le=2147483647)]
ExactRequiredText = Annotated[str, BeforeValidator(_exact_required_text)]
ManualOptionalText = Annotated[str | None, BeforeValidator(_optional_text)]
StoredOptionalText = Annotated[str | None, BeforeValidator(_stored_optional_text)]


class _PartModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)


class ManualServicePartCreate(_PartModel):
    source: Literal["manual"]
    name: VehicleText
    part_number: ManualOptionalText = None
    manufacturer: ManualOptionalText = None
    quantity: PositiveInteger = 1
    notes: ManualOptionalText = None


class CatalogPartLookup(_PartModel):
    manufacturer: ExactRequiredText
    part_number: ExactRequiredText


class CatalogPartPreview(_PartModel):
    id: PositiveInteger
    manufacturer: ExactRequiredText
    part_number: ExactRequiredText
    name: ExactRequiredText
    category: ExactRequiredText


class CatalogServicePartCreate(_PartModel):
    source: Literal["catalog"]
    preview: CatalogPartPreview
    quantity: PositiveInteger = 1
    notes: ManualOptionalText = None


ServicePartCreate = Annotated[
    ManualServicePartCreate | CatalogServicePartCreate, Field(discriminator="source"),
]


class ServicePartSnapshot(_PartModel):
    id: PositiveInteger
    service_record_id: PositiveInteger
    part_id: PositiveInteger | None
    name: ExactRequiredText
    part_number: StoredOptionalText
    manufacturer: StoredOptionalText
    quantity: PositiveInteger
    notes: StoredOptionalText


class ServicePartListResponse(_PartModel):
    vehicle_id: PositiveInteger
    service_record_id: PositiveInteger
    parts: list[ServicePartSnapshot]

    @model_validator(mode="after")
    def require_matching_service(self) -> Self:
        if any(part.service_record_id != self.service_record_id for part in self.parts):
            raise ValueError("Part snapshots must match the requested service record.")
        return self


class ServicePartRemovalRequest(_PartModel):
    confirm_removal: bool

    @field_validator("confirm_removal")
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError(PART_REMOVAL_ERROR)
        return value


class ServicePartRemovalResponse(_PartModel):
    id: PositiveInteger
    service_record_id: PositiveInteger
    deleted: bool

    @field_validator("deleted")
    @classmethod
    def require_removed(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Removal response must confirm deletion.")
        return value
