import copy
import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from app import vehicle_schemas
from app.vehicle_schemas import (
    CONFIRMATION_ERROR,
    EMPTY_PATCH_ERROR,
    REQUIRED_PATCH_ERROR,
    VEHICLE_ID_ERROR,
    ReadingConfirmationRequired,
    Vehicle,
    VehicleCreate,
    VehicleId,
    VehiclePatch,
    require_reading_confirmation,
    validate_vehicle_id,
)


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture(autouse=True)
def fixed_year(monkeypatch):
    monkeypatch.setattr(vehicle_schemas, "get_current_year", lambda: 2026)


@pytest.fixture
def current_vehicle():
    return Vehicle(
        id=123, year=2020, make="Honda", model="CRF250R", vehicle_type="Dirt bike",
        engine=None, mileage=Decimal("1000.0"), operating_hours=Decimal("10.0"),
        readings_updated_at=datetime(2026, 11, 14, tzinfo=timezone.utc),
        created_at=datetime(2026, 11, 13, tzinfo=timezone.utc),
    )


@pytest.mark.parametrize("raw", ["1", "42", "2147483647"])
def test_canonical_id_accepts_integer_storage_boundaries(raw):
    assert validate_vehicle_id(raw) == int(raw)
    assert TypeAdapter(VehicleId).validate_python(raw) == int(raw)


@pytest.mark.parametrize(
    "raw",
    ["", "0", "00", "01", "000123", "+1", "-1", "-0", "1.0", "1.1", "1e1",
     " 1", "1 ", "\t1", "1\n", "1\r\n", "1\u00a0", "\u0661", "\uff11", "1_0",
     "1,000", "123abc", "abc", "2147483648", "9999999999", "10000000000",
     "1\x00", "\ud800", "%31", None, True, False, 1, 1.0, Decimal("1"), b"1", [], {},
     pytest.param("9" * 10000, id="overlong-id")],
)
def test_canonical_id_rejects_noncanonical_forms_with_one_fixed_message(raw):
    with pytest.raises(ValueError) as caught:
        validate_vehicle_id(raw)
    assert str(caught.value) == VEHICLE_ID_ERROR
    with pytest.raises(ValidationError) as caught:
        TypeAdapter(VehicleId).validate_python(raw)
    # Bare adapter errors still need the Step 3 boundary's input/context removal.
    error = caught.value.errors(include_input=False, include_context=False)[0]
    assert error["type"] == "value_error"
    assert error["msg"] == "Value error, " + VEHICLE_ID_ERROR
    assert "input" not in error and "ctx" not in error


@pytest.mark.parametrize("fields", [{}, {"reading_confirmation": {}}, {"reading_confirmation": {"mileage": "1"}}])
def test_patch_requires_at_least_one_business_field(fields):
    with pytest.raises(ValidationError, match=EMPTY_PATCH_ERROR):
        VehiclePatch.model_validate(fields)


@pytest.mark.parametrize("raw", [None, [], "Honda", 123, True])
def test_patch_requires_json_object(raw):
    with pytest.raises(ValidationError):
        VehiclePatch.model_validate_json(json.dumps(raw))


def test_malformed_json_is_rejected():
    with pytest.raises(ValidationError) as caught:
        VehiclePatch.model_validate_json('{"make":')
    assert caught.value.errors(include_input=False)[0]["type"] == "json_invalid"


@pytest.mark.parametrize("field", ["user_id", "owner_id", "id", "created_at", "readings_updated_at", "token", "unknown"])
def test_patch_rejects_ownership_readonly_and_unknown_fields(field):
    with pytest.raises(ValidationError) as caught:
        VehiclePatch.model_validate({"make": "Honda", field: "not-accepted"})
    assert caught.value.errors(include_input=False)[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize("field", ["year", "make", "model", "vehicle_type"])
def test_required_fields_cannot_be_cleared(field):
    with pytest.raises(ValidationError) as caught:
        VehiclePatch.model_validate({field: None})
    error = caught.value.errors(include_input=False)[0]
    assert error["loc"] == (field,)
    assert error["msg"] == "Value error, " + REQUIRED_PATCH_ERROR


def test_omission_is_not_an_explicit_null():
    request = VehiclePatch(make="  Honda  ")
    assert request.model_fields_set == {"make"}
    assert request.changes() == {"make": "Honda"}
    assert request.model_dump(exclude_unset=True) == {"make": "Honda"}
    assert request.engine is None and request.mileage is None and request.year is None
    clear = VehiclePatch(engine=None, mileage=None, operating_hours=None)
    assert clear.model_fields_set == {"engine", "mileage", "operating_hours"}
    assert clear.changes() == {"engine": None, "mileage": None, "operating_hours": None}


@pytest.mark.parametrize("year", [1886, 2026, 2027])
def test_patch_accepts_inclusive_year_boundaries(year):
    assert VehiclePatch(year=year).changes() == {"year": year}


@pytest.mark.parametrize("year", [1885, 2028, 0, -1, 32768, True, False, "2020", 2020.0])
def test_patch_year_rejects_policy_and_strict_type_violations(year):
    with pytest.raises(ValidationError):
        VehiclePatch(year=year)


def test_create_and_patch_use_same_live_testable_year_provider(monkeypatch):
    calendar = [2030]
    monkeypatch.setattr(vehicle_schemas, "get_current_year", lambda: calendar[0])
    create = {"make": "Honda", "model": "Civic", "vehicle_type": "Car"}
    for model, fields in [(VehiclePatch, {}), (VehicleCreate, create)]:
        assert model(**fields, year=2031).year == 2031
        with pytest.raises(ValidationError, match="1886 through 2031"):
            model(**fields, year=2032)
    calendar[0] = 2031
    assert VehiclePatch(year=2032).year == 2032
    assert VehicleCreate(**create, year=2032).year == 2032


@pytest.mark.parametrize("year", [1, 1885, 2028, 32767])
def test_omitted_legacy_year_does_not_block_unrelated_edit(year, current_vehicle, monkeypatch):
    current = Vehicle.model_validate({**dict(current_vehicle), "year": year})
    before = copy.deepcopy(current)

    def must_not_check_calendar():
        pytest.fail("An omitted year must not invoke create/PATCH year policy")

    monkeypatch.setattr(vehicle_schemas, "get_current_year", must_not_check_calendar)
    patch = VehiclePatch(make="  Updated make  ")
    require_reading_confirmation(current, patch)
    assert patch.changes() == {"make": "Updated make"}
    assert current == before and current.year == year


@pytest.mark.parametrize("year", [1, 1885, 2028, 32767])
def test_explicit_unchanged_legacy_year_still_has_to_meet_input_policy(year):
    with pytest.raises(ValidationError):
        VehiclePatch(year=year)


@pytest.mark.parametrize("field", ["make", "model", "vehicle_type", "engine"])
def test_patch_reuses_trim_case_and_unicode_rules(field):
    request = VehiclePatch.model_validate({field: "  H\u00f6nda e\u0301 \U0001f6f5 Custom\n"})
    assert request.changes() == {field: "H\u00f6nda e\u0301 \U0001f6f5 Custom"}


@pytest.mark.parametrize("field", ["make", "model", "vehicle_type"])
@pytest.mark.parametrize("value", ["", " \t\n", 123, True, [], {}, b"Car"])
def test_patch_required_text_rejects_blank_and_wrong_types(field, value):
    with pytest.raises(ValidationError):
        VehiclePatch.model_validate({field: value})


@pytest.mark.parametrize("field", ["make", "model", "vehicle_type", "engine"])
@pytest.mark.parametrize("value", ["bad\x00text", "bad\ud800text", "bad\udffftext"])
def test_patch_rejects_nul_and_invalid_unicode_even_in_json(field, value):
    with pytest.raises(ValidationError):
        VehiclePatch.model_validate_json(json.dumps({field: value}))


@pytest.mark.parametrize("value", [None, "", " \t\n"])
def test_patch_blank_or_null_engine_is_an_explicit_clear(value):
    request = VehiclePatch(engine=value)
    assert request.changes() == {"engine": None}
    assert request.model_fields_set == {"engine"}


@pytest.mark.parametrize("value", [123, True, [], {}, b"V8"])
def test_patch_engine_rejects_nontext(value):
    with pytest.raises(ValidationError):
        VehiclePatch(engine=value)


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("raw,canonical", [("0", "0.0"), ("000.0", "0.0"), ("12", "12.0"), (" \t012.3\n", "12.3"), ("99999999999.9", "99999999999.9")])
def test_patch_retains_decimal_bindings_and_serializes_canonically(field, raw, canonical):
    request = VehiclePatch.model_validate({field: raw})
    assert request.changes() == {field: Decimal(canonical)}
    assert isinstance(request.changes()[field], Decimal)
    assert request.model_dump(exclude_unset=True) == {field: canonical}
    assert json.loads(request.model_dump_json(exclude_unset=True)) == {field: canonical}


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("value", [0, 12.3, True, Decimal("1.0"), "", " ", "-0.0", "-1", "+1", "1e2", "NaN", "Infinity", "1,000", ".1", "1.", "1.00", "0.01", "100000000000.0", "\u0661.0", "1\x00", [], {}, b"1.0"])
def test_patch_rejects_invalid_readings_without_rounding(field, value):
    with pytest.raises(ValidationError):
        VehiclePatch.model_validate({field: value})


@pytest.mark.parametrize("mileage,hours", [(None, None), (None, "0"), ("0", None), ("0", "0"), ("123.4", "10")])
def test_patch_preserves_independent_null_and_confirmed_zero(mileage, hours):
    request = VehiclePatch(mileage=mileage, operating_hours=hours)
    expected = {"mileage": None if mileage is None else Decimal(mileage),
                "operating_hours": None if hours is None else Decimal(hours)}
    assert request.changes() == expected


@pytest.mark.parametrize("value", [None, [], "yes", True, 1])
def test_confirmation_must_be_a_strict_object(value):
    with pytest.raises(ValidationError, match=CONFIRMATION_ERROR):
        VehiclePatch(mileage="9", reading_confirmation=value)


@pytest.mark.parametrize("value", [None, 0, 1.0, True, "", "-1", "1.00", "NaN", "100000000000.0"])
@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
def test_confirmation_requires_nonnull_valid_decimal_strings(field, value):
    with pytest.raises(ValidationError):
        VehiclePatch.model_validate({field: "9", "reading_confirmation": {field: value}})


@pytest.mark.parametrize("key", ["owner_id", "user_id", "year", "engine", "unknown", "mileage\x00"])
def test_confirmation_rejects_unknown_and_nonreading_keys(key):
    with pytest.raises(ValidationError) as caught:
        VehiclePatch(mileage="9", reading_confirmation={key: "10"})
    assert caught.value.errors(include_input=False)[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
def test_confirmation_cannot_acknowledge_an_omitted_reading(field):
    with pytest.raises(ValidationError, match=CONFIRMATION_ERROR):
        VehiclePatch(make="Honda", reading_confirmation={field: "10"})


def test_confirmation_is_request_only_and_never_in_business_values(current_vehicle):
    request = VehiclePatch(mileage="900", reading_confirmation={"mileage": " 01000.0 "})
    assert request.changes() == {"mileage": Decimal("900")}
    assert request.reading_confirmation.mileage == Decimal("1000")
    assert request.model_dump(exclude_unset=True) == {
        "mileage": "900.0", "reading_confirmation": {"mileage": "1000.0"},
    }
    with pytest.raises(ValidationError):
        Vehicle.model_validate({**dict(current_vehicle), "reading_confirmation": {}})


def test_empty_confirmation_mapping_is_no_acknowledgment(current_vehicle):
    request = VehiclePatch(mileage="900", reading_confirmation={})
    with pytest.raises(ReadingConfirmationRequired):
        require_reading_confirmation(current_vehicle, request)


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("old,new,required", [(None, None, False), (None, "0", False), (None, "10", False), ("0", None, True), ("0", "0", False), ("10", None, True), ("10", "9.9", True), ("10", "10.0", False), ("10", "10.1", False)])
def test_reading_transition_rules_are_pure_and_null_safe(field, old, new, required, current_vehicle):
    current = Vehicle.model_validate({**dict(current_vehicle), field: None if old is None else Decimal(old)})
    patch = VehiclePatch.model_validate({field: new})
    before_current, before_patch = copy.deepcopy(current), copy.deepcopy(patch)
    if required:
        with pytest.raises(ReadingConfirmationRequired) as caught:
            require_reading_confirmation(current, patch)
        assert caught.value.fields == (field,)
        assert caught.value.current_readings == {field: format(Decimal(old), ".1f")}
        assert str(caught.value) == "Reading changes require confirmation."
    else:
        assert require_reading_confirmation(current, patch) is None
    assert current == before_current and patch == before_patch
    assert patch.model_fields_set == before_patch.model_fields_set


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("new", [None, "0", "9.9"])
def test_matching_confirmation_allows_clear_or_lower_without_mutation(field, new, current_vehicle):
    current = Vehicle.model_validate({**dict(current_vehicle), field: Decimal("10.0")})
    patch = VehiclePatch.model_validate({field: new, "reading_confirmation": {field: "010"}})
    before = copy.deepcopy(current)
    assert require_reading_confirmation(current, patch) is None
    assert current == before


@pytest.mark.parametrize("confirmed", [{}, {"mileage": "1000"}, {"operating_hours": "10"}, {"mileage": "999", "operating_hours": "10"}])
def test_both_required_readings_are_reported_without_partial_changes(confirmed, current_vehicle):
    patch = VehiclePatch(make="Changed", mileage=None, operating_hours="9", reading_confirmation=confirmed)
    before = copy.deepcopy(current_vehicle)
    with pytest.raises(ReadingConfirmationRequired) as caught:
        require_reading_confirmation(current_vehicle, patch)
    assert caught.value.fields == ("mileage", "operating_hours")
    assert caught.value.current_readings == {"mileage": "1000.0", "operating_hours": "10.0"}
    assert current_vehicle == before
    assert "1000" not in str(caught.value) and "Changed" not in str(caught.value)


def test_matching_both_confirmations_succeeds_without_applying_patch(current_vehicle):
    patch = VehiclePatch(make="Changed", mileage=None, operating_hours="9", reading_confirmation={"mileage": "1000", "operating_hours": "10"})
    before = copy.deepcopy(current_vehicle)
    require_reading_confirmation(current_vehicle, patch)
    assert current_vehicle == before
    assert "reading_confirmation" not in patch.changes()


@pytest.mark.parametrize("field", ["mileage", "operating_hours"])
@pytest.mark.parametrize("current,required", [("1200", True), ("800", False), ("900", False), (None, False)])
def test_confirmation_is_rechecked_against_each_fresh_snapshot(field, current, required, current_vehicle):
    patch = VehiclePatch.model_validate({field: "900", "reading_confirmation": {field: "1000"}})
    original = Vehicle.model_validate({**dict(current_vehicle), field: Decimal("1000")})
    require_reading_confirmation(original, patch)
    fresh = Vehicle.model_validate({**dict(current_vehicle), field: None if current is None else Decimal(current)})
    before = copy.deepcopy(fresh)
    with pytest.raises(ReadingConfirmationRequired) as caught:
        require_reading_confirmation(fresh, patch)
    assert caught.value.fields == ((field,) if required else ())
    assert caught.value.current_readings == ({field: "1200.0"} if required else {})
    assert fresh == before


def test_stale_nondangerous_acknowledgment_reports_only_other_required_reading(current_vehicle):
    fresh = Vehicle.model_validate({**dict(current_vehicle), "mileage": Decimal("800")})
    patch = VehiclePatch(mileage="900", operating_hours=None, reading_confirmation={"mileage": "1000", "operating_hours": "10"})
    with pytest.raises(ReadingConfirmationRequired) as caught:
        require_reading_confirmation(fresh, patch)
    assert caught.value.fields == ("operating_hours",)
    assert caught.value.current_readings == {"operating_hours": "10.0"}


def test_all_valid_equal_business_values_are_a_nonempty_noop(current_vehicle):
    patch = VehiclePatch(year=2020, make="Honda", model="CRF250R", engine=None, vehicle_type="Dirt bike", mileage="1000.0", operating_hours="10")
    before = copy.deepcopy(current_vehicle)
    require_reading_confirmation(current_vehicle, patch)
    assert all(value == getattr(current_vehicle, name) for name, value in patch.changes().items())
    assert len(patch.changes()) == 7 and current_vehicle == before


def test_validation_exception_strings_hide_raw_patch_and_confirmation_values():
    private = "synthetic-private-invalid-value"
    for fields in [{"mileage": private}, {"make": "Honda", "reading_confirmation": {"mileage": private}}]:
        with pytest.raises(ValidationError) as caught:
            VehiclePatch.model_validate(fields)
        assert private not in str(caught.value)
        # The HTTP boundary must still remove raw input and context in Step 3.
        for error in caught.value.errors(include_input=False, include_context=False):
            assert "input" not in error and "ctx" not in error


def test_patch_input_json_schema_matches_supplied_null_rules():
    schema = VehiclePatch.model_json_schema()
    assert not schema.get("required") and schema["additionalProperties"] is False
    assert schema["properties"]["year"]["type"] == "integer"
    for name in ["make", "model", "vehicle_type"]:
        assert schema["properties"][name]["type"] == "string"
    for name in ["mileage", "operating_hours"]:
        assert schema["properties"][name]["anyOf"] == [{"type": "string"}, {"type": "null"}]
    confirmation = schema["$defs"]["ReadingConfirmation"]
    assert confirmation["additionalProperties"] is False
    assert all(confirmation["properties"][name]["type"] == "string" for name in ["mileage", "operating_hours"])
