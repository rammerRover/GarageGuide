import json
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app import vehicle_schemas
from app.vehicle_schemas import Vehicle, VehicleCreate, VehicleListResponse


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture(autouse=True)
def fixed_calendar(monkeypatch):
    class Calendar:
        @staticmethod
        def today():
            return date(2026, 11, 13)

    monkeypatch.setattr(vehicle_schemas, "date", Calendar)


@pytest.fixture
def create_fields():
    return {"year": 2020, "make": "Honda", "model": "CRF250R", "vehicle_type": "Dirt bike"}


@pytest.fixture
def stored_fields(create_fields):
    return {
        **create_fields, "id": 123, "engine": None,
        "mileage": None, "operating_hours": Decimal("0.0"),
        "readings_updated_at": datetime(2026, 11, 13, 18, tzinfo=timezone.utc),
        "created_at": datetime(2026, 11, 13, 18, tzinfo=timezone.utc),
    }


def test_year_provider_uses_backend_calendar():
    assert vehicle_schemas.get_current_year() == 2026


@pytest.mark.parametrize("year", [1886, 2026, 2027])
def test_create_accepts_inclusive_year_boundaries(year, create_fields):
    assert VehicleCreate(**{**create_fields, "year": year}).year == year


@pytest.mark.parametrize("year", [1885, 2028, 0, -1, 32768, True, False, "2020", 2020.0, None])
def test_create_rejects_year_outside_policy_or_wrong_type(year, create_fields):
    with pytest.raises(ValidationError):
        VehicleCreate(**{**create_fields, "year": year})


def test_year_limit_is_evaluated_for_each_request(monkeypatch, create_fields):
    monkeypatch.setattr(vehicle_schemas, "get_current_year", lambda: 2030)
    assert VehicleCreate(**{**create_fields, "year": 2031}).year == 2031
    with pytest.raises(ValidationError, match="1886 through 2031"):
        VehicleCreate(**{**create_fields, "year": 2032})
    monkeypatch.setattr(vehicle_schemas, "get_current_year", lambda: 2031)
    assert VehicleCreate(**{**create_fields, "year": 2032}).year == 2032


@pytest.mark.parametrize("field", ["year", "make", "model", "vehicle_type"])
def test_create_requires_fields(field, create_fields):
    del create_fields[field]
    with pytest.raises(ValidationError):
        VehicleCreate(**create_fields)


@pytest.mark.parametrize("field", ["make", "model", "vehicle_type"])
@pytest.mark.parametrize("value", ["", " \t\r\n", None, True, 123, b"Honda", [], {}])
def test_required_text_rejects_blank_or_nontext(field, value, create_fields):
    with pytest.raises(ValidationError):
        VehicleCreate(**{**create_fields, field: value})


@pytest.mark.parametrize("field", ["make", "model", "vehicle_type", "engine"])
def test_text_trims_surroundings_and_preserves_case_and_unicode(field, create_fields):
    value = "  \tH\u00f6nda e\u0301 \U0001f6f5 Custom\n"
    request = VehicleCreate(**{**create_fields, field: value})
    assert getattr(request, field) == "H\u00f6nda e\u0301 \U0001f6f5 Custom"


@pytest.mark.parametrize("engine", [None, "", " \t\n"])
def test_unknown_engine_becomes_null(engine, create_fields):
    assert VehicleCreate(**{**create_fields, "engine": engine}).engine is None


@pytest.mark.parametrize("engine", [True, 123, [], {}, b"V8"])
def test_engine_rejects_nontext(engine, create_fields):
    with pytest.raises(ValidationError):
        VehicleCreate(**{**create_fields, "engine": engine})


@pytest.mark.parametrize("field", ["make", "model", "vehicle_type", "engine"])
@pytest.mark.parametrize("value", ["\x00Honda", "Honda\x00", "bad\ud800text", "bad\udffftext"])
def test_text_rejects_nul_and_unpaired_surrogates(field, value, create_fields):
    with pytest.raises(ValidationError, match="valid Unicode characters without NUL"):
        VehicleCreate(**{**create_fields, field: value})


def test_json_escaped_invalid_unicode_is_rejected(create_fields):
    with pytest.raises(ValidationError):
        VehicleCreate.model_validate_json(json.dumps({**create_fields, "make": "bad\ud800"}))


@pytest.mark.parametrize("field", ["user_id", "owner_id", "id", "created_at", "readings_updated_at", "other"])
def test_create_forbids_ownership_readonly_and_unknown_fields(field, create_fields):
    with pytest.raises(ValidationError) as caught:
        VehicleCreate(**{**create_fields, field: "not-accepted"})
    assert caught.value.errors(include_input=False)[0]["type"] == "extra_forbidden"


def test_optional_fields_default_to_unknown(create_fields):
    request = VehicleCreate(**create_fields)
    assert request.engine is None
    assert request.mileage is None
    assert request.operating_hours is None


@pytest.mark.parametrize(
    ("mileage", "hours"), [(None, None), ("0.0", None), (None, "0.0"), ("12000.1", "25.5")]
)
def test_independent_readings_preserve_unknown_and_zero(mileage, hours, create_fields):
    request = VehicleCreate(**{**create_fields, "mileage": mileage, "operating_hours": hours})
    output = request.model_dump(mode="json")
    assert output["mileage"] == mileage
    assert output["operating_hours"] == hours
    assert (request.mileage is None) == (mileage is None)
    assert (request.operating_hours is None) == (hours is None)
    if mileage is not None:
        assert isinstance(request.mileage, Decimal)
    if hours is not None:
        assert isinstance(request.operating_hours, Decimal)


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize(
    ("value", "expected"),
    [("0", "0.0"), ("000.0", "0.0"), ("12", "12.0"), (" \t012.3\n", "12.3"),
     ("99999999999.9", "99999999999.9")],
)
def test_readings_use_exact_decimal_and_canonical_serialization(field, value, expected, create_fields):
    request = VehicleCreate(**{**create_fields, field: value})
    assert getattr(request, field) == Decimal(expected)
    assert request.model_dump()[field] == expected
    assert json.loads(request.model_dump_json())[field] == expected


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize(
    "value",
    [0, 12.3, True, False, Decimal("1.0"), "", " ", "-0.0", "-1", "+1", "1e2", "NaN",
     "Infinity", "1,000", ".1", "1.", "1.00", "0.01", "100000000000.0", "\u0661.0",
     "1\x00", "\ud800", [], {}, b"1.0"],
)
def test_create_rejects_invalid_reading_without_rounding(field, value, create_fields):
    with pytest.raises(ValidationError):
        VehicleCreate(**{**create_fields, field: value})


def test_json_numbers_are_not_coerced_to_decimal_strings(create_fields):
    with pytest.raises(ValidationError):
        VehicleCreate.model_validate_json(json.dumps({**create_fields, "mileage": 0}))
    request = VehicleCreate.model_validate_json(json.dumps({**create_fields, "mileage": "0.0"}))
    assert request.mileage == Decimal("0.0")


def test_request_json_schema_advertises_string_or_null_readings():
    fields = VehicleCreate.model_json_schema()["properties"]
    for field in ("mileage", "operating_hours"):
        assert fields[field]["anyOf"] == [{"type": "string"}, {"type": "null"}]


def test_validation_exception_text_hides_raw_input(create_fields):
    value = "private-invalid-reading"
    with pytest.raises(ValidationError) as caught:
        VehicleCreate(**{**create_fields, "mileage": value})
    assert value not in str(caught.value)
    # The later HTTP boundary must still sanitize errors(), which includes raw input by default.
    assert all("input" not in entry for entry in caught.value.errors(include_input=False))


def test_public_vehicle_has_exact_fields_and_decimal_strings(stored_fields):
    vehicle = Vehicle(**stored_fields)
    assert json.loads(vehicle.model_dump_json()) == {
        "id": 123, "year": 2020, "make": "Honda", "model": "CRF250R",
        "engine": None, "vehicle_type": "Dirt bike", "mileage": None,
        "operating_hours": "0.0", "readings_updated_at": "2026-11-13T18:00:00Z",
        "created_at": "2026-11-13T18:00:00Z",
    }


@pytest.mark.parametrize("year", [1, 1885, 2028, 32767])
def test_stored_years_outside_create_policy_remain_readable(year, stored_fields):
    assert Vehicle(**{**stored_fields, "year": year}).year == year


@pytest.mark.parametrize("year", [0, -1, 32768, True, "2020", 2020.0])
def test_response_still_enforces_smallint_storage_bounds_and_types(year, stored_fields):
    with pytest.raises(ValidationError):
        Vehicle(**{**stored_fields, "year": year})


@pytest.mark.parametrize("vehicle_id", [0, -1, True, "123", 123.0])
def test_response_requires_positive_strict_integer_id(vehicle_id, stored_fields):
    with pytest.raises(ValidationError):
        Vehicle(**{**stored_fields, "id": vehicle_id})


@pytest.mark.parametrize("field", ["created_at", "readings_updated_at"])
def test_response_rejects_naive_timestamps(field, stored_fields):
    with pytest.raises(ValidationError):
        Vehicle(**{**stored_fields, field: datetime(2026, 11, 13)})


def test_response_allows_unknown_readings_and_reading_timestamp(stored_fields):
    vehicle = Vehicle(**{
        **stored_fields, "operating_hours": None, "readings_updated_at": None,
    })
    assert vehicle.model_dump(mode="json")["mileage"] is None
    assert vehicle.model_dump(mode="json")["operating_hours"] is None
    assert vehicle.readings_updated_at is None


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize(
    "value", [Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-1.0"),
              Decimal("0.01"), Decimal("100000000000.0"), 1.0, True],
)
def test_response_rejects_invalid_stored_readings(field, value, stored_fields):
    with pytest.raises(ValidationError):
        Vehicle(**{**stored_fields, field: value})


def test_response_serialization_never_rounds(stored_fields):
    vehicle = Vehicle(**{
        **stored_fields, "mileage": Decimal("99999999999.9"), "operating_hours": Decimal("12"),
    })
    assert vehicle.model_dump(mode="json")["mileage"] == "99999999999.9"
    assert vehicle.model_dump(mode="json")["operating_hours"] == "12.0"


def test_stored_signed_zero_serializes_as_confirmed_zero(stored_fields):
    vehicle = Vehicle(**{**stored_fields, "mileage": Decimal("-0.0")})
    assert vehicle.model_dump(mode="json")["mileage"] == "0.0"


@pytest.mark.parametrize("field", ["user_id", "password_hash", "session_id", "token"])
def test_response_rejects_nonpublic_fields(field, stored_fields):
    with pytest.raises(ValidationError):
        Vehicle(**{**stored_fields, field: "not-public"})


def test_list_response_supports_empty_and_exact_public_vehicles(stored_fields):
    assert VehicleListResponse(vehicles=[]).model_dump() == {"vehicles": []}
    response = VehicleListResponse(vehicles=[Vehicle(**stored_fields)])
    assert response.model_dump(mode="json") == {"vehicles": [Vehicle(**stored_fields).model_dump(mode="json")]}
    with pytest.raises(ValidationError):
        VehicleListResponse(vehicles=[], user_id=1)
