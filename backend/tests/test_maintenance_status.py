from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from app.maintenance_schedule_schemas import MaintenanceSchedule
from app.maintenance_status import DayLimitStatus, ReadingLimitStatus, calculate_maintenance_status
from app.vehicle_schemas import Vehicle


pytestmark = pytest.mark.usefixtures("forbid_database")
TODAY = date(2026, 11, 24)
NOW = datetime(2026, 11, 24, 18, tzinfo=UTC)


def saved_vehicle(**changes):
    return Vehicle(**{
        "id": 7, "year": 2020, "make": "Synthetic", "model": "Test", "vehicle_type": "Car",
        "engine": None, "mileage": None, "operating_hours": None,
        "readings_updated_at": NOW, "created_at": NOW,
        **changes,
    })


def saved_schedule(**changes):
    return MaintenanceSchedule(**{
        "id": 12, "vehicle_id": 7, "name": "Oil change",
        "interval_days": None, "baseline_date": None,
        "interval_miles": None, "baseline_mileage": None,
        "interval_hours": None, "baseline_hours": None,
        "source_notes": None, "created_at": NOW,
        **changes,
    })


@pytest.mark.parametrize(("today", "remaining", "status"), [
    (date(2026, 11, 23), 1, "upcoming"),
    (date(2026, 11, 24), 0, "due"),
    (date(2026, 11, 25), -1, "overdue"),
])
def test_calendar_threshold_uses_the_supplied_date_and_signed_days(today, remaining, status):
    task = saved_schedule(interval_days=4, baseline_date=date(2026, 11, 20))
    result = calculate_maintenance_status(saved_vehicle(), [task], as_of_date=today, now=NOW)
    entry = result.model_dump(mode="json")["schedules"][0]

    assert result.as_of_date == today
    assert entry["status"] == status
    assert entry["limits"] == [{
        "kind": "days", "status": status, "due_value": "2026-11-24", "remaining": remaining, "issue": None,
    }]


@pytest.mark.parametrize(("kind", "interval", "baseline", "field"), [
    ("mileage", "interval_miles", "baseline_mileage", "mileage"),
    ("hours", "interval_hours", "baseline_hours", "operating_hours"),
])
@pytest.mark.parametrize(("current", "remaining", "status", "issue"), [
    (Decimal("0.2"), "0.1", "upcoming", None),
    (Decimal("0.3"), "0.0", "due", None),
    (Decimal("0.4"), "-0.1", "overdue", None),
    (Decimal("0.0"), None, "needs_information", "below_baseline"),
    (None, None, "needs_information", "missing_reading"),
])
def test_reading_thresholds_use_exact_decimal_strings(kind, interval, baseline, field, current, remaining, status, issue):
    task = saved_schedule(**{interval: Decimal("0.2"), baseline: Decimal("0.1")})
    vehicle = saved_vehicle(**{field: current})
    result = calculate_maintenance_status(vehicle, [task], as_of_date=TODAY, now=NOW)
    entry = result.model_dump(mode="json")["schedules"][0]

    assert entry["status"] == status
    assert entry["limits"] == [{
        "kind": kind, "status": status, "due_value": "0.3", "remaining": remaining, "issue": issue,
    }]


@pytest.mark.parametrize(("day_offset", "miles", "hours", "overall", "in_order"), [
    (0, Decimal("10.1"), Decimal("2.0"), "overdue", ["due", "overdue", "due"]),
    (1, Decimal("10.0"), None, "overdue", ["overdue", "due", "needs_information"]),
    (0, None, Decimal("1.9"), "due", ["due", "needs_information", "upcoming"]),
    (-1, Decimal("10.0"), None, "due", ["upcoming", "due", "needs_information"]),
    (-1, Decimal("9.9"), None, "needs_information", ["upcoming", "upcoming", "needs_information"]),
    (-1, Decimal("0.0"), Decimal("0.0"), "upcoming", ["upcoming", "upcoming", "upcoming"]),
])
def test_combined_precedence_preserves_all_limit_results(day_offset, miles, hours, overall, in_order):
    task = saved_schedule(
        interval_days=4, baseline_date=date(2026, 11, 20),
        interval_miles=Decimal("10.0"), baseline_mileage=Decimal("0.0"),
        interval_hours=Decimal("2.0"), baseline_hours=Decimal("0.0"),
    )
    vehicle = saved_vehicle(mileage=miles, operating_hours=hours)
    entry = calculate_maintenance_status(
        vehicle, [task], as_of_date=TODAY + timedelta(days=day_offset), now=NOW,
    ).schedules[0]

    assert entry.status == overall
    assert [limit.kind for limit in entry.limits] == ["days", "mileage", "hours"]
    assert [limit.status for limit in entry.limits] == in_order


def test_target_and_remaining_can_exceed_the_input_column_range_exactly():
    maximum = Decimal("99999999999.9")
    task = saved_schedule(interval_miles=maximum, baseline_mileage=maximum)
    vehicle = saved_vehicle(mileage=maximum)
    with localcontext() as context:
        context.prec = 5
        result = calculate_maintenance_status(vehicle, [task], as_of_date=TODAY, now=NOW).model_dump(mode="json")

    assert result["schedules"][0]["limits"] == [{
        "kind": "mileage", "status": "upcoming", "due_value": "199999999999.8",
        "remaining": "99999999999.9", "issue": None,
    }]


def test_missing_reading_still_exposes_the_exact_target_above_the_input_range():
    maximum = Decimal("99999999999.9")
    task = saved_schedule(interval_hours=maximum, baseline_hours=maximum)
    result = calculate_maintenance_status(saved_vehicle(), [task], as_of_date=TODAY, now=NOW).schedules[0]
    assert result.limits[0].model_dump(mode="json") == {
        "kind": "hours", "status": "needs_information", "due_value": "199999999999.8",
        "remaining": None, "issue": "missing_reading",
    }


@pytest.mark.parametrize(("interval", "due_date", "remaining", "status"), [
    (1, date.max, 0, "due"),
    (2, None, 1, "upcoming"),
    (2147483647, None, 2147483646, "upcoming"),
])
def test_calendar_overflow_retains_exact_remaining_days_and_the_baseline(interval, due_date, remaining, status):
    baseline = date(9999, 12, 30)
    task = saved_schedule(interval_days=interval, baseline_date=baseline)
    entry = calculate_maintenance_status(saved_vehicle(), [task], as_of_date=date.max, now=NOW).schedules[0]

    assert entry.status == status
    assert entry.limits[0].due_value == due_date
    assert entry.limits[0].remaining == remaining
    assert entry.limits[0].issue is None
    assert (entry.schedule.baseline_date, entry.schedule.interval_days) == (baseline, interval)


def test_unusable_baselines_affect_only_enabled_limits():
    task = saved_schedule(
        interval_days=1, baseline_date=TODAY + timedelta(days=1),
        interval_miles=Decimal("5.0"), baseline_mileage=None,
        baseline_hours=Decimal("1.0"),
    )
    entry = calculate_maintenance_status(saved_vehicle(), [task], as_of_date=TODAY, now=NOW).schedules[0]

    assert entry.status == "needs_information"
    assert [limit.kind for limit in entry.limits] == ["days", "mileage"]
    assert all(limit.issue == "invalid_baseline" and limit.due_value is None and limit.remaining is None
               for limit in entry.limits)


@pytest.mark.parametrize(("timestamp", "warning"), [
    (None, "missing"),
    (NOW + timedelta(microseconds=1), "future"),
    (NOW, None),
    (NOW.astimezone(timezone(timedelta(hours=9))), None),
    (NOW - timedelta(days=30) + timedelta(microseconds=1), None),
    (NOW - timedelta(days=30), "at_least_30_days_old"),
    (NOW - timedelta(days=30, microseconds=1), "at_least_30_days_old"),
])
def test_timestamp_warnings_never_change_the_same_saved_reading_results(timestamp, warning):
    vehicle = saved_vehicle(mileage=Decimal("10.0"), operating_hours=Decimal("5.0"))
    tasks = [
        saved_schedule(id=4, interval_hours=Decimal("1.0"), baseline_hours=Decimal("5.0")),
        saved_schedule(id=2, interval_miles=Decimal("1.0"), baseline_mileage=Decimal("9.0")),
        saved_schedule(id=6, interval_hours=Decimal("1.0"), baseline_hours=Decimal("0.0")),
        saved_schedule(id=5, interval_miles=Decimal("1.0"), baseline_mileage=Decimal("20.0")),
    ]
    expected = calculate_maintenance_status(vehicle, tasks, as_of_date=TODAY, now=NOW)
    result = calculate_maintenance_status(
        vehicle.model_copy(update={"readings_updated_at": timestamp}), tasks, as_of_date=TODAY, now=NOW,
    )

    assert result.readings_timestamp_warning == warning
    assert result.schedules == expected.schedules
    assert [(item.schedule.id, item.status) for item in result.schedules] == [
        (2, "due"), (4, "upcoming"), (5, "needs_information"), (6, "overdue"),
    ]


class _SpringOffset(tzinfo):
    def utcoffset(self, value):
        # A deterministic offset change without requiring an installed time-zone database.
        return timedelta(hours=-6 if value.month == 3 else -5)


@pytest.mark.parametrize(("hours", "warning"), [(12, None), (13, "at_least_30_days_old")])
def test_elapsed_time_crossing_an_offset_change_is_compared_in_utc(hours, warning):
    zone = _SpringOffset()
    old = datetime(2026, 3, 15, 12, tzinfo=zone)
    now = datetime(2026, 4, 14, hours, tzinfo=zone)
    result = calculate_maintenance_status(saved_vehicle(readings_updated_at=old), [], as_of_date=now.date(), now=now)

    assert result.readings_timestamp_warning == warning


def test_the_evaluation_clock_requires_an_aware_instant():
    with pytest.raises(ValueError, match="aware clock instant"):
        calculate_maintenance_status(saved_vehicle(), [], as_of_date=TODAY, now=NOW.replace(tzinfo=None))


def test_empty_snapshot_preserves_the_public_vehicle_and_captured_date():
    vehicle = saved_vehicle(mileage=Decimal("0.0"), readings_updated_at=None)
    payload = calculate_maintenance_status(vehicle, [], as_of_date=TODAY, now=NOW).model_dump(mode="json")
    assert payload == {
        "vehicle": vehicle.model_dump(mode="json"), "schedules": [],
        "as_of_date": TODAY.isoformat(), "readings_timestamp_warning": "missing",
    }
    assert payload["vehicle"]["mileage"] == "0.0"


def test_public_snapshot_rejects_a_schedule_for_a_different_vehicle():
    foreign = saved_schedule(vehicle_id=8, interval_days=1, baseline_date=TODAY)
    with pytest.raises(ValidationError, match="Schedules must match the status vehicle"):
        calculate_maintenance_status(saved_vehicle(), [foreign], as_of_date=TODAY, now=NOW)


@pytest.mark.parametrize(("model", "values"), [
    (DayLimitStatus, {"status": "due", "due_value": TODAY, "remaining": "0", "issue": None}),
    (ReadingLimitStatus, {"kind": "hours", "status": "due", "due_value": 0.3, "remaining": Decimal("0"), "issue": None}),
    (ReadingLimitStatus, {"kind": "mileage", "status": "soon", "due_value": None, "remaining": None, "issue": None}),
])
def test_public_limit_models_validate_wire_source_types(model, values):
    with pytest.raises(ValidationError):
        model(**values)
