import json
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from app.service_part_schemas import (
    SERVICE_PART_ID_ERROR, CatalogPartLookup, CatalogPartPreview,
    CatalogServicePartCreate, ManualServicePartCreate, ServicePartCreate,
    ServicePartId, ServicePartListResponse, ServicePartRemovalRequest,
    ServicePartRemovalResponse, ServicePartSnapshot, validate_service_part_id,
)


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture
def preview():
    return {"id": 123, "manufacturer": "Example Maker", "part_number": "EX-123",
            "name": "Example filter", "category": "Filters"}


@pytest.fixture
def snapshot():
    return {"id": 9, "service_record_id": 8, "part_id": None, "name": "Filter",
            "part_number": None, "manufacturer": None, "quantity": 1, "notes": None}


@pytest.mark.parametrize("value", ["1", "9", "2147483647"])
def test_canonical_path_ids(value):
    assert validate_service_part_id(value) == int(value)
    assert TypeAdapter(ServicePartId).validate_python(value) == int(value)


@pytest.mark.parametrize("value", [
    "", "0", "00", "01", "+1", "-1", "1.0", "1/2", "1e2", " 1", "1 ", "1\n",
    "١", "１", "2147483648", "99999999999999999999999", "no-id", None, 1, True, 1.0,
])
def test_invalid_path_ids_use_fixed_error(value):
    with pytest.raises(ValueError, match=SERVICE_PART_ID_ERROR):
        validate_service_part_id(value)
    with pytest.raises(ValidationError):
        TypeAdapter(ServicePartId).validate_python(value)


def test_manual_minimum_input_defaults_and_public_fields():
    record = ManualServicePartCreate(source="manual", name="  Filter  ")
    assert record.model_dump(mode="json") == {
        "source": "manual", "name": "Filter", "part_number": None,
        "manufacturer": None, "quantity": 1, "notes": None,
    }


def test_catalog_quantity_default_and_null_notes(preview):
    record = CatalogServicePartCreate(source="catalog", preview=preview)
    assert record.quantity == 1 and record.notes is None
    assert record.preview.model_dump(mode="json") == preview


@pytest.mark.parametrize("quantity", [1, 2, 2147483647])
@pytest.mark.parametrize("source", ["manual", "catalog"])
def test_quantity_bounds_and_integer_json_roundtrip(quantity, source, preview):
    fields = {"source": source, "quantity": quantity}
    fields.update({"name": "Filter"} if source == "manual" else {"preview": preview})
    result = TypeAdapter(ServicePartCreate).validate_json(json.dumps(fields))
    assert result.quantity == quantity and type(result.quantity) is int
    assert result.model_dump(mode="json")["quantity"] == quantity


@pytest.mark.parametrize("quantity", [
    None, True, False, "1", "", "2.5", "one", 0, -1, 2147483648,
    1.0, 1.5, Decimal("1"), float("inf"), float("nan"), [], {},
])
@pytest.mark.parametrize("model", [ManualServicePartCreate, CatalogServicePartCreate])
def test_invalid_quantities_are_not_coerced(model, quantity, preview):
    fields = {"source": "manual", "name": "Filter"} if model is ManualServicePartCreate else {
        "source": "catalog", "preview": preview,
    }
    with pytest.raises(ValidationError):
        model(**fields, quantity=quantity)


@pytest.mark.parametrize("field", ["part_number", "manufacturer", "notes"])
@pytest.mark.parametrize("value", [None, "", " \t\n", "\u0085\u001c\u2003"])
def test_manual_optional_empty_values_become_null(field, value):
    record = ManualServicePartCreate(source="manual", name="Filter", **{field: value})
    assert getattr(record, field) is None


def test_manual_unicode_preserves_case_feff_and_interior_text():
    text = "\ufeffMixed Case\t\n" + " " * 32768 + "After\ufeff"
    record = ManualServicePartCreate(
        source="manual", name="\u0085" + text + "\u001c",
        part_number="  Ex-01 ", manufacturer=" Maker ", notes="\u001f" + text + "\u2003",
    )
    assert record.name == record.notes == text
    assert record.part_number == "Ex-01" and record.manufacturer == "Maker"
    assert ManualServicePartCreate(source="manual", name="\ufeff").name == "\ufeff"


@pytest.mark.parametrize("value", ["", " \t\n", None, 123, True, [], {}])
def test_manual_name_must_be_nonblank_text(value):
    with pytest.raises(ValidationError):
        ManualServicePartCreate(source="manual", name=value)


@pytest.mark.parametrize("field", ["name", "part_number", "manufacturer", "notes"])
@pytest.mark.parametrize("value", ["bad\x00text", "bad\ud800", "bad\udfff"])
def test_manual_invalid_unicode_and_nul(field, value):
    fields = {"source": "manual", "name": "Filter", field: value}
    with pytest.raises(ValidationError):
        ManualServicePartCreate(**fields)


@pytest.mark.parametrize("field", ["part_number", "manufacturer", "notes"])
@pytest.mark.parametrize("value", [1, True, 1.0, [], {}])
def test_manual_optional_fields_reject_nontext(field, value):
    with pytest.raises(ValidationError):
        ManualServicePartCreate(source="manual", name="Filter", **{field: value})


@pytest.mark.parametrize("field", ["manufacturer", "part_number"])
def test_exact_lookup_preserves_original_identity(field):
    fields = {"manufacturer": "Maker", "part_number": "Ex-123"}
    value = " \u0085\ufeffMiXeD e\u0301\t\nText\ufeff\u001f "
    fields[field] = value
    lookup = CatalogPartLookup(**fields)
    assert lookup.model_dump() == fields
    changed = {**fields, field: value.lower()}
    assert CatalogPartLookup(**changed).model_dump() != lookup.model_dump()


@pytest.mark.parametrize("field", ["manufacturer", "part_number"])
@pytest.mark.parametrize("value", [None, "", "\t\u0085\u001c", 1, True, "bad\0text", "\udfff"])
def test_lookup_rejects_invalid_identity_json(field, value):
    fields = {"manufacturer": "Maker", "part_number": "EX-1", field: value}
    with pytest.raises(ValidationError):
        CatalogPartLookup.model_validate_json(json.dumps(fields))


@pytest.mark.parametrize("field", ["manufacturer", "part_number", "name", "category"])
def test_preview_preserves_all_reviewed_identity_fields(preview, field):
    preview[field] = " \ufeffMiXeD\t\nIdentity\ufeff "
    assert CatalogPartPreview(**preview).model_dump(mode="json") == preview
    created = CatalogServicePartCreate(source="catalog", preview=preview, notes="  note  ")
    assert created.preview.model_dump(mode="json") == preview
    assert created.notes == "note"


@pytest.mark.parametrize("field", ["manufacturer", "part_number", "name", "category"])
@pytest.mark.parametrize("value", [None, "", "\t \u0085\u001c", 1, True, "x\0y", "\ud800"])
def test_preview_requires_safe_nonblank_identity(preview, field, value):
    with pytest.raises(ValidationError):
        CatalogPartPreview(**{**preview, field: value})


@pytest.mark.parametrize("model,fields", [
    (ManualServicePartCreate, {"source": "manual", "name": "Filter"}),
    (CatalogPartLookup, {"manufacturer": "Maker", "part_number": "EX-1"}),
    (CatalogPartPreview, {"id": 1, "manufacturer": "Maker", "part_number": "EX-1", "name": "Filter", "category": "Filters"}),
    (CatalogServicePartCreate, {"source": "catalog", "preview": {"id": 1, "manufacturer": "Maker", "part_number": "EX-1", "name": "Filter", "category": "Filters"}}),
])
def test_every_required_request_field_is_required(model, fields):
    for field in fields:
        with pytest.raises(ValidationError):
            model(**{key: value for key, value in fields.items() if key != field})


@pytest.mark.parametrize("extra", ["user_id", "owner_id", "vehicle_id", "service_record_id", "part_id", "category", "cost", "created_at", "unknown"])
def test_manual_rejects_ownership_readonly_and_extra_fields(extra):
    with pytest.raises(ValidationError):
        ManualServicePartCreate(source="manual", name="Filter", **{extra: 1})


def test_discriminator_requires_explicit_source_and_rejects_mixed_inputs(preview):
    adapter = TypeAdapter(ServicePartCreate)
    assert isinstance(adapter.validate_python({"source": "manual", "name": "Filter"}), ManualServicePartCreate)
    assert isinstance(adapter.validate_python({"source": "catalog", "preview": preview}), CatalogServicePartCreate)
    for fields in [
        {"name": "Filter"}, {"source": "MANUAL", "name": "Filter"},
        {"source": None, "name": "Filter"}, {"source": "saved", "id": 1},
        {"source": "manual", "name": "Filter", "preview": preview},
        {"source": "catalog", "preview": preview, "name": "Client override"},
        {"source": "catalog", "preview": {**preview, "user_id": 1}},
    ]:
        with pytest.raises(ValidationError):
            adapter.validate_python(fields)


@pytest.mark.parametrize("value", [0, -1, 2147483648, True, "1", 1.0, None])
def test_preview_id_is_a_strict_database_integer(preview, value):
    with pytest.raises(ValidationError):
        CatalogPartPreview(**{**preview, "id": value})


def test_snapshot_exact_shape_null_reference_and_read_preservation(snapshot):
    snapshot.update(name=" \ufeffFilter\t ", part_number="", manufacturer=" Maker ", notes=" \u0085\ufeff\n ")
    record = ServicePartSnapshot(**snapshot)
    assert record.model_dump(mode="json") == snapshot
    restored = ServicePartSnapshot.model_validate_json(record.model_dump_json())
    assert restored == record
    assert ServicePartSnapshot(**{**snapshot, "part_id": 123}).name == record.name


@pytest.mark.parametrize("field", ["id", "service_record_id", "part_id", "quantity"])
@pytest.mark.parametrize("value", [0, -1, 2147483648, True, "1", 1.0])
def test_public_integer_fields_are_strict(snapshot, field, value):
    with pytest.raises(ValidationError):
        ServicePartSnapshot(**{**snapshot, field: value})


def test_snapshot_requires_every_public_field(snapshot):
    for field in snapshot:
        with pytest.raises(ValidationError):
            ServicePartSnapshot(**{key: value for key, value in snapshot.items() if key != field})


@pytest.mark.parametrize("field", ["source", "origin", "category", "created_at", "user_id", "vehicle_id", "cost"])
def test_snapshot_has_no_invented_public_fields(snapshot, field):
    with pytest.raises(ValidationError):
        ServicePartSnapshot(**snapshot, **{field: "unexpected"})


@pytest.mark.parametrize("field", ["name", "part_number", "manufacturer", "notes"])
@pytest.mark.parametrize("value", ["bad\x00text", "\udfff", 123, True])
def test_snapshot_text_must_be_safe(snapshot, field, value):
    with pytest.raises(ValidationError):
        ServicePartSnapshot(**{**snapshot, field: value})


def test_empty_and_populated_list_shapes_and_matching_parent(snapshot):
    assert ServicePartListResponse(vehicle_id=7, service_record_id=8, parts=[]).model_dump(mode="json") == {
        "vehicle_id": 7, "service_record_id": 8, "parts": [],
    }
    data = {"vehicle_id": 7, "service_record_id": 8, "parts": [snapshot, {**snapshot, "id": 10}]}
    assert ServicePartListResponse(**data).model_dump(mode="json") == data
    with pytest.raises(ValidationError):
        ServicePartListResponse(**{**data, "parts": [snapshot, {**snapshot, "service_record_id": 9}]})


@pytest.mark.parametrize("value", [None, False, 1, 0, "true", "false", "1", 1.0, [], {}])
def test_removal_accepts_only_explicit_boolean_true(value):
    with pytest.raises(ValidationError):
        ServicePartRemovalRequest.model_validate_json(json.dumps({"confirm_removal": value}))


def test_removal_request_is_required_and_has_no_metadata():
    assert ServicePartRemovalRequest.model_validate_json('{"confirm_removal":true}').model_dump() == {
        "confirm_removal": True,
    }
    for fields in [{}, {"confirm_removal": True, "id": 9}, {"confirm_removal": True, "force": True}]:
        with pytest.raises(ValidationError):
            ServicePartRemovalRequest(**fields)


def test_removal_response_requires_exact_shape_and_true():
    data = {"id": 9, "service_record_id": 8, "deleted": True}
    assert ServicePartRemovalResponse(**data).model_dump(mode="json") == data
    for fields in [{**data, "deleted": False}, {**data, "deleted": 1},
                   {**data, "user_id": 1}, {"id": 9, "deleted": True}]:
        with pytest.raises(ValidationError):
            ServicePartRemovalResponse(**fields)


@pytest.mark.parametrize("model,fields", [
    (ManualServicePartCreate, {"source": "manual", "name": "synthetic-private-text\x00"}),
    (CatalogPartLookup, {"manufacturer": "synthetic-private-text\x00", "part_number": "EX-1"}),
])
def test_model_error_representation_hides_raw_input(model, fields):
    with pytest.raises(ValidationError) as caught:
        model(**fields)
    assert "synthetic-private-text" not in str(caught.value)


@pytest.mark.parametrize("quantity", [None, True, "1", 1.0, 0, 2147483648])
@pytest.mark.parametrize("source", ["manual", "catalog"])
def test_json_create_quantities_are_strict(quantity, source, preview):
    fields = {"source": source, "quantity": quantity}
    fields.update({"name": "Filter"} if source == "manual" else {"preview": preview})
    with pytest.raises(ValidationError):
        TypeAdapter(ServicePartCreate).validate_json(json.dumps(fields))


def test_all_model_boundaries_forbid_unapproved_fields(preview, snapshot):
    cases = [
        (CatalogPartLookup, {"manufacturer": "Maker", "part_number": "EX-1"}),
        (CatalogPartPreview, preview),
        (CatalogServicePartCreate, {"source": "catalog", "preview": preview}),
        (ServicePartListResponse, {"vehicle_id": 7, "service_record_id": 8, "parts": []}),
        (ServicePartSnapshot, snapshot),
        (ServicePartRemovalRequest, {"confirm_removal": True}),
        (ServicePartRemovalResponse, {"id": 9, "service_record_id": 8, "deleted": True}),
    ]
    for model, fields in cases:
        with pytest.raises(ValidationError):
            model.model_validate_json(json.dumps({**fields, "owner_id": 1}))


def test_catalog_notes_use_manual_normalization_and_preserve_feff(preview):
    for notes in [None, "", "\u0085\u001c\t "]:
        assert CatalogServicePartCreate(source="catalog", preview=preview, notes=notes).notes is None
    assert CatalogServicePartCreate(source="catalog", preview=preview, notes=" \ufeffnote\ufeff ").notes == "\ufeffnote\ufeff"


@pytest.mark.parametrize("value", [None, "", "\t\u0085\u001c"])
def test_public_name_cannot_be_cleared(snapshot, value):
    with pytest.raises(ValidationError):
        ServicePartSnapshot(**{**snapshot, "name": value})


def test_list_parent_ids_are_strict_and_required():
    valid = {"vehicle_id": 7, "service_record_id": 8, "parts": []}
    for field in valid:
        with pytest.raises(ValidationError):
            ServicePartListResponse(**{key: value for key, value in valid.items() if key != field})
    for field in ["vehicle_id", "service_record_id"]:
        for value in [None, 0, -1, 2147483648, True, "1", 1.0]:
            with pytest.raises(ValidationError):
                ServicePartListResponse(**{**valid, field: value})
