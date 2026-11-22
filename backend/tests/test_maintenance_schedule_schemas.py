from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from app import maintenance_schedule_schemas as schemas
from app.maintenance_schedule_schemas import (
    DuplicateScheduleNameResponse, MaintenanceSchedule, MaintenanceScheduleCreate,
    MaintenanceScheduleListResponse, MaintenanceSchedulePatch, ScheduleId,
)


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(schemas, "get_current_date", lambda: date(2026, 11, 21))


@pytest.fixture
def stored_fields():
    return {
        "id": 23,
        "vehicle_id": 7,
        "name": "Oil change",
        "interval_days": 365,
        "interval_miles": Decimal("5000.0"),
        "interval_hours": None,
        "baseline_date": date(2026, 2, 1),
        "baseline_mileage": Decimal("0.0"),
        "baseline_hours": None,
        "source_notes": "Owner log",
        "created_at": datetime(2026, 2, 2, 16, tzinfo=timezone.utc),
    }


@pytest.mark.parametrize("pairs,serialized", [
    ({"interval_days": 2147483647, "baseline_date": "0001-01-01"},
     {"interval_days": 2147483647, "baseline_date": "0001-01-01"}),
    ({"interval_miles": "99999999999.9", "baseline_mileage": "0"},
     {"interval_miles": "99999999999.9", "baseline_mileage": "0.0"}),
    ({"interval_hours": "0.1", "baseline_hours": "99999999999.9"},
     {"interval_hours": "0.1", "baseline_hours": "99999999999.9"}),
    ({"interval_days": 1, "baseline_date": "2026-11-21", "interval_miles": "30", "baseline_mileage": "0.0",
      "interval_hours": "2", "baseline_hours": "0"},
     {"interval_days": 1, "baseline_date": "2026-11-21", "interval_miles": "30.0", "baseline_mileage": "0.0",
      "interval_hours": "2.0", "baseline_hours": "0.0"}),
])
def test_create_accepts_single_and_combined_pairs_with_exact_wire_values(pairs, serialized):
    request = MaintenanceScheduleCreate(name="  Oil Change  ", source_notes="  Own log\nPage 2  ", **pairs)
    payload = request.model_dump(mode="json", exclude_unset=True)
    assert payload == {"name": "Oil Change", "source_notes": "Own log\nPage 2", **serialized}
    assert MaintenanceScheduleCreate.model_validate(payload) == request


@pytest.mark.parametrize("fields,locations", [
    ({}, {"interval_days"}),
    ({"interval_days": 1}, {"baseline_date"}),
    ({"interval_miles": "1"}, {"baseline_mileage"}),
    ({"interval_hours": "1"}, {"baseline_hours"}),
    ({"interval_days": 1, "interval_miles": "1", "interval_hours": "1"},
     {"baseline_date", "baseline_mileage", "baseline_hours"}),
    ({"interval_days": 1, "baseline_date": "2024-02-29", "baseline_mileage": "0"}, {"baseline_mileage"}),
    ({"baseline_hours": "0"}, {"baseline_hours"}),
])
def test_create_reports_missing_or_inactive_baselines_by_field(fields, locations):
    with pytest.raises(ValidationError) as caught:
        MaintenanceScheduleCreate(name="Task", **fields)
    assert {error["loc"] for error in caught.value.errors()} == {(field,) for field in locations}


@pytest.mark.parametrize("day", [0, -1, 2147483648, True, 1.0, "30"])
def test_invalid_day_interval_is_rejected(day):
    with pytest.raises(ValidationError) as caught:
        MaintenanceScheduleCreate(name="Task", interval_days=day, baseline_date="2024-02-29")
    assert caught.value.errors()[0]["loc"] == ("interval_days",)


@pytest.mark.parametrize("field,value", [
    ("interval_miles", "0"), ("interval_hours", "0.0"), ("interval_miles", "-0.1"),
    ("interval_miles", "0.01"), ("interval_hours", "1e2"), ("interval_hours", "Infinity"),
    ("interval_miles", "100000000000.0"), ("interval_miles", 1), ("interval_hours", 1.0),
    ("baseline_mileage", "0.01"), ("baseline_mileage", "100000000000.0"),
    ("baseline_hours", True), ("baseline_hours", "-1"), ("baseline_hours", "NaN"),
])
def test_invalid_decimals_are_rejected_by_field(field, value):
    with pytest.raises(ValidationError) as caught:
        MaintenanceSchedulePatch.model_validate({field: value})
    assert caught.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize("value", ["", "2026-11-22", "2025-02-29", "2026-1-01", "20260101",
                                  "2026-W01-1", "2026-01-01T00:00:00", True, date(2026, 1, 1)])
def test_baseline_date_rejects_future_invalid_and_noncanonical_values(value):
    with pytest.raises(ValidationError) as caught:
        MaintenanceSchedulePatch(baseline_date=value)
    assert caught.value.errors()[0]["loc"] == ("baseline_date",)


def test_patch_keeps_omitted_values_and_applies_explicit_nulls(stored_fields):
    current = MaintenanceSchedule(**stored_fields)
    patch = MaintenanceSchedulePatch(interval_miles=None, baseline_mileage=None, source_notes=None)
    assert patch.model_dump(mode="json", exclude_unset=True) == {
        "interval_miles": None, "baseline_mileage": None, "source_notes": None,
    }
    merged = patch.merged_values(current)
    assert merged == {
        field: None if field in patch.model_fields_set else stored_fields[field]
        for field in schemas.EDITABLE_FIELDS
    }
    assert current.baseline_mileage == Decimal("0.0")


def test_partial_patch_uses_stored_counterpart_and_keeps_native_types(stored_fields):
    current = MaintenanceSchedule(**stored_fields)
    patch = MaintenanceSchedulePatch(interval_miles="6000", reviewed_duplicate_ids=[24])
    merged = patch.merged_values(current)
    assert merged["interval_miles"] == Decimal("6000")
    assert isinstance(merged["interval_miles"], Decimal)
    assert merged["baseline_mileage"] == Decimal("0.0")
    assert merged["baseline_date"] == date(2026, 2, 1)
    assert "reviewed_duplicate_ids" not in merged


@pytest.mark.parametrize("patch,locations", [
    ({"baseline_mileage": None}, {"baseline_mileage"}),
    ({"interval_miles": None}, {"baseline_mileage"}),
    ({"interval_hours": "0.1"}, {"baseline_hours"}),
    ({"interval_days": None, "baseline_date": None, "interval_miles": None, "baseline_mileage": None},
     {"interval_days"}),
])
def test_invalid_final_pair_combinations_fail_after_merge(stored_fields, patch, locations):
    edit = MaintenanceSchedulePatch(**patch)
    with pytest.raises(ValidationError) as caught:
        edit.merged_values(MaintenanceSchedule(**stored_fields))
    assert {error["loc"] for error in caught.value.errors()} == {(field,) for field in locations}


def test_legacy_snapshot_keeps_inactive_baseline_and_text_until_corrected(stored_fields):
    current = MaintenanceSchedule(**{**stored_fields, "baseline_hours": Decimal("9.0"),
                                     "name": "  Oil change  ", "source_notes": "  Old notes  "})
    payload = current.model_dump(mode="json")
    assert payload["interval_hours"] is None and payload["baseline_hours"] == "9.0"
    assert payload["name"] == "  Oil change  " and payload["source_notes"] == "  Old notes  "
    with pytest.raises(ValidationError) as caught:
        MaintenanceSchedulePatch(source_notes="New notes").merged_values(current)
    assert caught.value.errors()[0]["loc"] == ("baseline_hours",)
    fixed = MaintenanceSchedulePatch(baseline_hours=None).merged_values(current)
    assert fixed["baseline_hours"] is None and fixed["source_notes"] == "  Old notes  "
    assert fixed["name"] == "  Oil change  "


def test_legacy_future_date_is_readable_and_must_be_corrected_on_write(stored_fields):
    current = MaintenanceSchedule(**{**stored_fields, "baseline_date": date(2027, 1, 1)})
    assert current.model_dump(mode="json")["baseline_date"] == "2027-01-01"
    with pytest.raises(ValidationError) as caught:
        MaintenanceSchedulePatch(name="Updated").merged_values(current)
    assert caught.value.errors()[0]["loc"] == ("baseline_date",)
    assert MaintenanceSchedulePatch(baseline_date="2026-11-21").merged_values(current)["baseline_date"] == date(2026, 11, 21)


@pytest.mark.parametrize("fields", [
    {}, {"reviewed_duplicate_ids": [24]}, {"name": None}, {"name": " "}, {"name": "a\x00b"},
    {"source_notes": "bad\ud800"}, {"vehicle_id": 7}, {"created_at": "2026-11-21"}, {"extra": False},
])
def test_rejects_empty_review_only_and_malformed_patches(fields):
    with pytest.raises(ValidationError):
        MaintenanceSchedulePatch.model_validate(fields)


@pytest.mark.parametrize("ids", [None, [], [24, 24], ["24"], [True], [1.0], [0], [2147483648], {"id": 24}])
def test_duplicate_review_requires_distinct_positive_integer_ids(ids):
    with pytest.raises(ValidationError) as caught:
        MaintenanceSchedulePatch(name="Task", reviewed_duplicate_ids=ids)
    assert caught.value.errors()[0]["loc"][0] == "reviewed_duplicate_ids"


def test_write_models_accept_review_ids_and_normalize_blank_notes():
    request = MaintenanceScheduleCreate(
        name="Task", interval_hours="1.0", baseline_hours="0.0", source_notes=" \n\t ", reviewed_duplicate_ids=[25, 24],
    )
    assert request.reviewed_duplicate_ids == [25, 24] and request.source_notes is None
    patch = MaintenanceSchedulePatch(source_notes="  ")
    assert patch.model_dump(exclude_unset=True) == {"source_notes": None}


@pytest.mark.parametrize("text,expected", [("1", 1), ("2147483647", 2147483647)])
def test_schedule_path_id_accepts_canonical_text(text, expected):
    assert TypeAdapter(ScheduleId).validate_python(text) == expected


@pytest.mark.parametrize("value", [1, "0001", "0", "2147483648", " 1", "+1", True, "1.0"])
def test_schedule_path_id_rejects_noncanonical_or_out_of_range_values(value):
    with pytest.raises(ValidationError, match="Enter a schedule ID"):
        TypeAdapter(ScheduleId).validate_python(value)


def test_public_responses_preserve_null_zero_and_owner_scope(stored_fields):
    record = MaintenanceSchedule(**stored_fields)
    encoded = record.model_dump(mode="json")
    assert encoded == {
        **stored_fields,
        "baseline_date": "2026-02-01",
        "interval_miles": "5000.0",
        "baseline_mileage": "0.0",
        "created_at": "2026-02-02T16:00:00Z",
    }
    assert MaintenanceSchedule.model_validate_json(record.model_dump_json()) == record
    assert MaintenanceScheduleListResponse(vehicle_id=7, schedules=[]).model_dump(mode="json") == {
        "vehicle_id": 7, "schedules": [],
    }
    assert MaintenanceScheduleListResponse(vehicle_id=7, schedules=[record]).model_dump(mode="json") == {
        "vehicle_id": 7, "schedules": [encoded],
    }
    with pytest.raises(ValidationError, match="match the requested vehicle"):
        MaintenanceScheduleListResponse(vehicle_id=8, schedules=[record])
    duplicate = DuplicateScheduleNameResponse(matches=[record])
    assert duplicate.model_dump(mode="json") == {
        "code": "duplicate_schedule_name", "detail": schemas.DUPLICATE_NAME_DETAIL, "matches": [encoded],
    }
    assert DuplicateScheduleNameResponse(matches=[]).model_dump(mode="json")["matches"] == []
