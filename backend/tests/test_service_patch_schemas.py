import copy
import json
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app import service_schemas
from app.service_schemas import ServiceCreate, ServicePatch, ServiceRecord, ServiceRemovalRequest


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(service_schemas, "get_current_date", lambda: date(2026, 11, 18))


@pytest.fixture
def current_record():
    return ServiceRecord(
        id=456, vehicle_id=123, service_date=date(2026, 11, 14), service_type="maintenance",
        description="Changed oil", mileage=Decimal("1000.0"), operating_hours=Decimal("10.0"),
        cost=Decimal("42.50"), notes="Saved notes",
        created_at=datetime(2026, 11, 18, 16, tzinfo=timezone.utc),
    )


def test_empty_patch_is_invalid():
    with pytest.raises(ValidationError, match=service_schemas.EMPTY_PATCH_ERROR):
        ServicePatch()


def test_omission_stays_separate_from_explicit_null():
    patch = ServicePatch(description="  Corrected description  ")
    assert patch.model_fields_set == {"description"}
    assert patch.changes() == {"description": "Corrected description"}
    assert patch.model_dump(exclude_unset=True) == {"description": "Corrected description"}
    assert patch.service_date is None and patch.mileage is None
    clear = ServicePatch(mileage=None, operating_hours=None, cost=None, notes=None)
    assert clear.changes() == {"mileage": None, "operating_hours": None, "cost": None, "notes": None}
    assert clear.model_fields_set == {"mileage", "operating_hours", "cost", "notes"}


@pytest.mark.parametrize("field", ["service_date", "service_type", "description"])
@pytest.mark.parametrize("value", [None, "", " \t\n"])
def test_required_fields_cannot_be_cleared(field, value):
    with pytest.raises(ValidationError):
        ServicePatch(**{field: value})


@pytest.mark.parametrize("field", ["mileage", "operating_hours", "cost"])
def test_numeric_null_clears_but_blank_wire_value_is_invalid(field):
    assert ServicePatch(**{field: None}).changes() == {field: None}
    with pytest.raises(ValidationError):
        ServicePatch(**{field: ""})


@pytest.mark.parametrize("value", [None, "", " \t\n"])
def test_blank_or_null_notes_are_explicit_clears(value):
    patch = ServicePatch(notes=value)
    assert patch.changes() == {"notes": None}
    assert patch.model_dump(exclude_unset=True) == {"notes": None}


@pytest.mark.parametrize("field", ["description", "notes"])
def test_patch_trims_without_changing_case_or_internal_formatting(field):
    text = "  R\u00e9paration e\u0301 \U0001f6f5\nSecond Line  "
    assert ServicePatch(**{field: text}).changes() == {field: text.strip()}


@pytest.mark.parametrize("field", ["description", "notes"])
@pytest.mark.parametrize("value", ["bad\x00text", "bad\ud800text", "bad\udffftext", True, 1, [], {}])
def test_patch_rejects_unsafe_or_nontext_values(field, value):
    with pytest.raises(ValidationError):
        ServicePatch(**{field: value})
    with pytest.raises(ValidationError):
        ServicePatch.model_validate_json(json.dumps({field: value}))


@pytest.mark.parametrize("field", ["id", "vehicle_id", "user_id", "owner_id", "created_at", "readings_updated_at", "total_cost", "reading_confirmation", "confirm_removal", "parts", "unknown"])
def test_patch_rejects_ownership_readonly_and_confirmation_metadata(field):
    with pytest.raises(ValidationError) as caught:
        ServicePatch(description="Correction", **{field: "not-accepted"})
    assert caught.value.errors(include_input=False)[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize("value", ["maintenance", "repair", "inspection", "diagnostic"])
def test_patch_accepts_all_schema_service_types(value):
    assert ServicePatch(service_type=value).changes() == {"service_type": value}


@pytest.mark.parametrize("value", ["Repair", "repair ", "custom", True, 1])
def test_patch_rejects_invalid_service_types(value):
    with pytest.raises(ValidationError):
        ServicePatch(service_type=value)


@pytest.mark.parametrize("value", ["0001-01-01", "2024-02-29", "2026-11-18"])
def test_patch_dates_use_create_rules_and_native_date_bindings(value):
    patch = ServicePatch(service_date=value)
    assert patch.changes() == {"service_date": date.fromisoformat(value)}
    assert patch.model_dump(mode="json", exclude_unset=True) == {"service_date": value}


@pytest.mark.parametrize("value", ["2026-11-19", "2025-02-29", "2026-1-01", "20261114", " 2026-11-14", "2026-11-14T00:00:00Z", date(2026, 11, 14), True])
def test_patch_dates_reject_future_noncanonical_and_coerced_values(value):
    with pytest.raises(ValidationError):
        ServicePatch(service_date=value)


def test_create_and_patch_use_the_same_live_calendar_provider(monkeypatch):
    today = [date(2030, 1, 1)]
    monkeypatch.setattr(service_schemas, "get_current_date", lambda: today[0])
    fields = {"service_type": "repair", "description": "Repair"}
    for model, other in ((ServiceCreate, fields), (ServicePatch, {})):
        with pytest.raises(ValidationError):
            model(**other, service_date="2030-01-02")
    today[0] = date(2030, 1, 2)
    assert ServiceCreate(**fields, service_date="2030-01-02").service_date == today[0]
    assert ServicePatch(service_date="2030-01-02").service_date == today[0]


def test_omitted_legacy_date_does_not_invoke_calendar_policy(current_record, monkeypatch):
    legacy = ServiceRecord.model_validate({**dict(current_record), "service_date": date(2099, 1, 1)})
    before = copy.deepcopy(legacy)

    def forbidden_calendar():
        pytest.fail("Omitted dates must not invoke create/PATCH date policy")

    monkeypatch.setattr(service_schemas, "get_current_date", forbidden_calendar)
    patch = ServicePatch(notes="Corrected notes")
    merged = {**dict(legacy), **patch.changes()}
    assert ServiceRecord.model_validate(merged).service_date == date(2099, 1, 1)
    assert legacy == before


def test_explicit_unchanged_future_date_must_still_meet_patch_policy():
    with pytest.raises(ValidationError):
        ServicePatch(service_date="2099-01-01")


@pytest.mark.parametrize("field,raw,expected", [
    ("mileage", " 001.2 ", "1.2"), ("operating_hours", "0", "0.0"),
    ("cost", "000.01", "0.01"), ("cost", "42.5", "42.50"),
    ("mileage", "99999999999.9", "99999999999.9"),
    ("cost", "9999999999.99", "9999999999.99"),
])
def test_patch_retains_decimal_bindings_and_serializes_canonical_strings(field, raw, expected):
    patch = ServicePatch(**{field: raw})
    assert patch.changes() == {field: Decimal(expected)}
    assert isinstance(patch.changes()[field], Decimal)
    assert patch.model_dump(exclude_unset=True) == {field: expected}
    assert json.loads(patch.model_dump_json(exclude_unset=True)) == {field: expected}


@pytest.mark.parametrize("field", ["mileage", "operating_hours", "cost"])
@pytest.mark.parametrize("value", [True, 0, 1.5, Decimal("1.0"), "-1", "+1", "1e2", "1,000", "0.001", "NaN", "Infinity", "100000000000.0", "\u0661.0", b"1.0", [], {}])
def test_patch_rejects_invalid_decimals_without_rounding(field, value):
    with pytest.raises(ValidationError):
        ServicePatch(**{field: value})


@pytest.mark.parametrize("field", ["mileage", "operating_hours", "cost"])
def test_zero_is_not_an_optional_clear(field):
    patch = ServicePatch(**{field: "0"})
    assert patch.changes()[field] == Decimal("0")
    assert patch.changes()[field] is not None


def test_historical_readings_can_be_lowered_or_cleared_without_odometer_confirmation(current_record):
    before = copy.deepcopy(current_record)
    patch = ServicePatch(mileage="1.0", operating_hours=None)
    assert patch.changes() == {"mileage": Decimal("1.0"), "operating_hours": None}
    assert current_record == before
    assert "reading_confirmation" not in ServicePatch.model_fields


def test_equal_supplied_values_remain_valid_for_later_locked_noop_comparison(current_record):
    before = copy.deepcopy(current_record)
    patch = ServicePatch(service_date="2026-11-14", description="  Changed oil  ", mileage="01000.0", cost="42.5")
    assert all(value == getattr(current_record, field) for field, value in patch.changes().items())
    assert current_record == before


@pytest.mark.parametrize("model", [ServiceCreate, ServicePatch, ServiceRemovalRequest])
@pytest.mark.parametrize("raw", [None, [], "text", 1, True])
def test_request_models_require_json_objects(model, raw):
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize("model", [ServiceCreate, ServicePatch, ServiceRemovalRequest])
def test_request_models_reject_malformed_json(model):
    with pytest.raises(ValidationError) as caught:
        model.model_validate_json('{"service_date":')
    assert caught.value.errors(include_input=False)[0]["type"] == "json_invalid"


def test_patch_exception_text_hides_raw_values():
    value = "private-invalid-cost"
    with pytest.raises(ValidationError) as caught:
        ServicePatch(cost=value)
    assert value not in str(caught.value)
    assert all("input" not in entry for entry in caught.value.errors(include_input=False))
