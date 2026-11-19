import json
from datetime import date, datetime, timezone
from decimal import Decimal
from itertools import product

import pytest
from pydantic import TypeAdapter, ValidationError

from app import service_schemas
from app.service_schemas import (
    SERVICE_ID_ERROR, ServiceCreate, ServiceId, ServiceListResponse, ServiceRecord,
    ServiceRemovalRequest, ServiceRemovalResponse, validate_service_id,
)
from app.vehicle_schemas import VehicleId


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    original = service_schemas.get_current_date
    monkeypatch.setattr(service_schemas, "get_current_date", lambda: date(2026, 11, 18))
    return original


@pytest.fixture
def create_fields():
    return {"service_date": "2026-11-14", "service_type": "maintenance", "description": "Changed oil"}


@pytest.fixture
def stored_fields():
    return {
        "id": 456, "vehicle_id": 123, "service_date": date(2026, 11, 14),
        "service_type": "maintenance", "description": "Changed oil", "mileage": Decimal("12500.0"),
        "operating_hours": None, "cost": Decimal("42.50"), "notes": None,
        "created_at": datetime(2026, 11, 18, 16, tzinfo=timezone.utc),
    }


def test_calendar_provider_uses_backend_local_date(monkeypatch, fixed_today):
    class Calendar(date):
        @classmethod
        def today(cls):
            return date(2032, 2, 29)

    monkeypatch.setattr(service_schemas, "date", Calendar)
    assert fixed_today() == date(2032, 2, 29)


@pytest.mark.parametrize("raw", ["1", "456", "2147483647"])
def test_ids_reuse_canonical_vehicle_rules(raw):
    assert validate_service_id(raw) == int(raw)
    assert TypeAdapter(ServiceId).validate_python(raw) == int(raw)
    assert TypeAdapter(VehicleId).validate_python(raw) == int(raw)


@pytest.mark.parametrize("raw", [
    "", "0", "00", "01", "+1", "-1", "1.0", "1e2", " 1", "1 ", "1\n", "\t1",
    "\u0661", "\uff11", "1_0", "1,000", "abc", "2147483648", "99999999999", "%31",
    "1\x00", "\ud800", None, True, False, 1, 1.0, Decimal("1"), b"1", [], {},
    pytest.param("9" * 10000, id="overlong-id"),
])
def test_invalid_service_ids_have_one_fixed_message(raw):
    with pytest.raises(ValueError) as caught:
        validate_service_id(raw)
    assert str(caught.value) == SERVICE_ID_ERROR
    with pytest.raises(ValidationError):
        TypeAdapter(ServiceId).validate_python(raw)


@pytest.mark.parametrize("value", ["0001-01-01", "2024-02-29", "2026-11-18"])
def test_create_accepts_calendar_boundaries_and_real_leap_day(value, create_fields):
    request = ServiceCreate(**{**create_fields, "service_date": value})
    assert request.service_date == date.fromisoformat(value)
    assert request.model_dump(mode="json")["service_date"] == value


@pytest.mark.parametrize("value", [
    "2026-11-19", "9999-12-31", "0000-01-01", "10000-01-01", "2025-02-29",
    "2026-13-01", "2026-04-31", "2026-00-01", "2026-01-00", "2026-1-01", "26-01-01",
    "20261114", "2026-W46-6", "2026-11-14T00:00:00Z", " 2026-11-14", "2026-11-14\n",
    "\u0662\u0660\u0662\u0666-11-14", "infinity", "", None, 0, True, b"2026-11-14",
    date(2026, 11, 14), datetime(2026, 11, 14, tzinfo=timezone.utc), [], {},
])
def test_create_rejects_invalid_or_future_dates_without_coercion(value, create_fields):
    with pytest.raises(ValidationError):
        ServiceCreate(**{**create_fields, "service_date": value})


def test_calendar_is_injected_and_rechecked_across_midnight(monkeypatch, create_fields):
    today = [date(2026, 12, 31)]
    monkeypatch.setattr(service_schemas, "get_current_date", lambda: today[0])
    fields = {**create_fields, "service_date": "2027-01-01"}
    with pytest.raises(ValidationError):
        ServiceCreate(**fields)
    today[0] = date(2027, 1, 1)
    assert ServiceCreate(**fields).service_date == today[0]


@pytest.mark.parametrize("field", ["service_date", "service_type", "description"])
def test_create_requires_business_fields(field, create_fields):
    del create_fields[field]
    with pytest.raises(ValidationError):
        ServiceCreate(**create_fields)


@pytest.mark.parametrize("value", ["maintenance", "repair", "inspection", "diagnostic"])
def test_service_types_match_existing_constraint(value, create_fields):
    assert ServiceCreate(**{**create_fields, "service_type": value}).service_type == value


@pytest.mark.parametrize("value", ["Maintenance", "repair ", " maintenance", "oil change", "", None, True, 1, [], {}])
def test_service_type_is_not_free_text_or_silently_normalized(value, create_fields):
    with pytest.raises(ValidationError):
        ServiceCreate(**{**create_fields, "service_type": value})


@pytest.mark.parametrize("value", ["", " \t\n", None, True, 123, b"Service", [], {}])
def test_description_requires_nonblank_strict_text(value, create_fields):
    with pytest.raises(ValidationError):
        ServiceCreate(**{**create_fields, "description": value})


@pytest.mark.parametrize("field", ["description", "notes"])
def test_text_preserves_case_unicode_and_internal_line_breaks(field, create_fields):
    text = "  \tR\u00e9paration e\u0301 \U0001f6f5\nSecond line  "
    request = ServiceCreate(**{**create_fields, field: text})
    assert getattr(request, field) == text.strip()


@pytest.mark.parametrize("field", ["description", "notes"])
@pytest.mark.parametrize("text", ["bad\x00text", "bad\ud800text", "bad\udffftext"])
def test_invalid_unicode_is_rejected_in_python_and_json(field, text, create_fields):
    fields = {**create_fields, field: text}
    with pytest.raises(ValidationError):
        ServiceCreate(**fields)
    with pytest.raises(ValidationError):
        ServiceCreate.model_validate_json(json.dumps(fields))


@pytest.mark.parametrize("notes", [None, "", " \t\n"])
def test_unknown_or_blank_notes_become_null(notes, create_fields):
    assert ServiceCreate(**{**create_fields, "notes": notes}).notes is None


@pytest.mark.parametrize("notes", [True, 1, [], {}, b"notes"])
def test_notes_do_not_coerce_nontext(notes, create_fields):
    with pytest.raises(ValidationError):
        ServiceCreate(**{**create_fields, "notes": notes})


def test_optional_values_default_to_unknown_and_no_text_cap_is_added(create_fields):
    request = ServiceCreate(**create_fields)
    assert all(getattr(request, field) is None for field in ("mileage", "operating_hours", "cost", "notes"))
    long_text = "Service details " * 1000
    assert ServiceCreate(**{**create_fields, "description": long_text}).description == long_text.strip()


@pytest.mark.parametrize("mileage,hours,cost", list(product([None, "0.0"], [None, "0.0"], [None, "0.00"])))
def test_unknown_readings_and_cost_remain_distinct_from_confirmed_zero(mileage, hours, cost, create_fields):
    request = ServiceCreate(**{**create_fields, "mileage": mileage, "operating_hours": hours, "cost": cost})
    output = request.model_dump(mode="json")
    assert (output["mileage"], output["operating_hours"], output["cost"]) == (mileage, hours, cost)
    for field in ("mileage", "operating_hours", "cost"):
        assert getattr(request, field) is None or isinstance(getattr(request, field), Decimal)


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("value,expected", [("0", "0.0"), ("000.0", "0.0"), (" 012.3 ", "12.3"), ("99999999999.9", "99999999999.9")])
def test_readings_reuse_exact_existing_decimal_rules(field, value, expected, create_fields):
    request = ServiceCreate(**{**create_fields, field: value})
    assert getattr(request, field) == Decimal(expected)
    assert request.model_dump(mode="json")[field] == expected


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("value", [0, True, 1.2, Decimal("1"), "", " ", "-0", "+1", "1e2", "1.00", "1.", ".1", "NaN", "Infinity", "100000000000.0", "\u0661.0", [], {}])
def test_invalid_readings_are_rejected_not_rounded(field, value, create_fields):
    with pytest.raises(ValidationError):
        ServiceCreate(**{**create_fields, field: value})


@pytest.mark.parametrize("value,expected", [
    ("0", "0.00"), ("000.00", "0.00"), (" 0012.3\n", "12.30"),
    ("42.50", "42.50"), ("0.01", "0.01"), ("9999999999.99", "9999999999.99"),
])
def test_cost_is_exact_two_decimal_usd_without_binary_math(value, expected, create_fields):
    request = ServiceCreate(**{**create_fields, "cost": value})
    assert request.cost == Decimal(expected)
    assert request.model_dump()["cost"] == expected
    assert json.loads(request.model_dump_json())["cost"] == expected


@pytest.mark.parametrize("value", [
    0, 0.01, True, False, Decimal("1.00"), "", " ", "-0.00", "-1", "+1", "1e2", "1,000",
    "NaN", "Infinity", ".01", "1.", "1.001", "1.000", "10000000000", "\u0661.00", "1\x00",
    "\ud800", b"1.00", [], {},
])
def test_invalid_cost_is_rejected_without_rounding(value, create_fields):
    with pytest.raises(ValidationError):
        ServiceCreate(**{**create_fields, "cost": value})


@pytest.mark.parametrize("field", ["id", "vehicle_id", "user_id", "owner_id", "created_at", "total_cost", "parts", "reading_confirmation", "unknown"])
def test_create_rejects_ownership_readonly_and_unapproved_fields(field, create_fields):
    with pytest.raises(ValidationError) as caught:
        ServiceCreate(**{**create_fields, field: "not-accepted"})
    assert caught.value.errors(include_input=False)[0]["type"] == "extra_forbidden"


def test_json_request_and_schema_preserve_decimal_strings(create_fields):
    request = ServiceCreate.model_validate_json(json.dumps({**create_fields, "cost": "0.01"}))
    assert request.cost == Decimal("0.01")
    with pytest.raises(ValidationError):
        ServiceCreate.model_validate_json(json.dumps({**create_fields, "cost": 0.01}))
    properties = ServiceCreate.model_json_schema()["properties"]
    for field in ("mileage", "operating_hours", "cost"):
        assert properties[field]["anyOf"] == [{"type": "string"}, {"type": "null"}]
    assert properties["service_date"]["type"] == "string"


def test_exception_text_hides_inputs_but_http_sanitization_is_still_needed(create_fields):
    value = "private-invalid-cost"
    with pytest.raises(ValidationError) as caught:
        ServiceCreate(**{**create_fields, "cost": value})
    assert value not in str(caught.value)
    assert "input" in caught.value.errors()[0]
    assert all("input" not in entry for entry in caught.value.errors(include_input=False))


def test_public_record_serializes_exact_approved_fields(stored_fields):
    assert json.loads(ServiceRecord(**stored_fields).model_dump_json()) == {
        "id": 456, "vehicle_id": 123, "service_date": "2026-11-14", "service_type": "maintenance",
        "description": "Changed oil", "mileage": "12500.0", "operating_hours": None,
        "cost": "42.50", "notes": None, "created_at": "2026-11-18T16:00:00Z",
    }


@pytest.mark.parametrize("stored_date", [date.min, date(2030, 1, 1), date.max])
def test_public_dates_do_not_apply_create_policy(stored_date, stored_fields, monkeypatch):
    def forbidden_calendar():
        pytest.fail("Stored service dates must not invoke create-time calendar policy")

    monkeypatch.setattr(service_schemas, "get_current_date", forbidden_calendar)
    record = ServiceRecord(**{**stored_fields, "service_date": stored_date})
    assert record.service_date == stored_date
    assert record.model_dump(mode="json")["service_date"] == stored_date.isoformat()


@pytest.mark.parametrize("value", ["infinity", "-infinity", "0000-01-01", "10000-01-01", "2026-11-14 BC"])
def test_unrepresentable_stored_dates_are_not_coerced_to_false_values(value, stored_fields):
    with pytest.raises(ValidationError):
        ServiceRecord.model_validate_json(json.dumps({**ServiceRecord(**stored_fields).model_dump(mode="json"), "service_date": value}))


@pytest.mark.parametrize("field", ["mileage", "operating_hours", "cost"])
@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-1"), Decimal("1000000000000"), Decimal("0.001")])
def test_public_numeric_values_must_fit_the_schema(field, value, stored_fields):
    with pytest.raises(ValidationError):
        ServiceRecord(**{**stored_fields, field: value})


@pytest.mark.parametrize("field", ["mileage", "operating_hours", "cost"])
def test_public_negative_decimal_zero_is_canonical_zero(field, stored_fields):
    record = ServiceRecord(**{**stored_fields, field: Decimal("-0.00")})
    assert record.model_dump(mode="json")[field] == ("0.00" if field == "cost" else "0.0")


@pytest.mark.parametrize("field", ["id", "vehicle_id"])
@pytest.mark.parametrize("value", [0, -1, 2147483648, True, "1", 1.0])
def test_public_ids_require_strict_positive_integer_storage_range(field, value, stored_fields):
    with pytest.raises(ValidationError):
        ServiceRecord(**{**stored_fields, field: value})


def test_public_timestamp_requires_timezone_and_all_public_fields_are_required(stored_fields):
    with pytest.raises(ValidationError):
        ServiceRecord(**{**stored_fields, "created_at": datetime(2026, 11, 18)})
    for field in stored_fields:
        fields = {name: value for name, value in stored_fields.items() if name != field}
        with pytest.raises(ValidationError):
            ServiceRecord(**fields)
    with pytest.raises(ValidationError):
        ServiceRecord(**stored_fields, user_id=999)


def test_list_shape_and_parent_matching_are_enforced(stored_fields):
    record = ServiceRecord(**stored_fields)
    assert ServiceListResponse(vehicle_id=123, services=[]).model_dump() == {"vehicle_id": 123, "services": []}
    response = ServiceListResponse(vehicle_id=123, services=[record])
    assert response.model_dump(mode="json") == {"vehicle_id": 123, "services": [record.model_dump(mode="json")]}
    with pytest.raises(ValidationError):
        ServiceListResponse(vehicle_id=124, services=[record])
    with pytest.raises(ValidationError):
        ServiceListResponse(vehicle_id=123, services=[], user_id=999)


def test_removal_requires_only_explicit_true():
    assert ServiceRemovalRequest(confirm_removal=True).model_dump() == {"confirm_removal": True}
    assert ServiceRemovalRequest.model_validate_json('{"confirm_removal":true}').confirm_removal is True


@pytest.mark.parametrize("value", [False, None, 0, 1, 1.0, "true", "True", "1", [], {}])
def test_removal_never_coerces_confirmation(value):
    with pytest.raises(ValidationError):
        ServiceRemovalRequest(confirm_removal=value)


def test_removal_rejects_missing_confirmation_and_force_options():
    with pytest.raises(ValidationError):
        ServiceRemovalRequest()
    for field in ("force", "user_id", "vehicle_id", "service_id"):
        with pytest.raises(ValidationError):
            ServiceRemovalRequest(confirm_removal=True, **{field: True})


def test_removal_response_is_exact_and_cannot_claim_failed_deletion():
    assert ServiceRemovalResponse(id=456, vehicle_id=123, deleted=True).model_dump() == {
        "id": 456, "vehicle_id": 123, "deleted": True,
    }
    for deleted in (False, None, 1, "true"):
        with pytest.raises(ValidationError):
            ServiceRemovalResponse(id=456, vehicle_id=123, deleted=deleted)
    with pytest.raises(ValidationError):
        ServiceRemovalResponse(id=456, vehicle_id=123, deleted=True, linked_count=1)
