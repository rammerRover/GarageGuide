from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.service_part_schemas import CatalogPartPreview, CatalogServicePartCreate, ManualServicePartCreate
from test_service_link_fixture_safety import linked_native
from test_session_fixture_safety import settings
import test_service_part_api_integration as native_api


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.mark.parametrize("failed_write", ["manual", "catalog"])
def test_positive_native_api_writer_registers_id_before_later_assertion_and_exact_cleanup(settings, monkeypatch, failed_write):
    native, connect = linked_native(settings)
    actor = SimpleNamespace(user=SimpleNamespace(id=42))
    first = SimpleNamespace(session=actor)
    vehicle, record = SimpleNamespace(id=8), SimpleNamespace(id=12)
    catalog = CatalogPartPreview(id=31, manufacturer="Synthetic maker", part_number="Synthetic number",
                                 name="Synthetic catalog snapshot", category="Synthetic")
    committed = {}
    one = SimpleNamespace(json=lambda: {"id": 22, "part_id": None, "quantity": 2147483647})
    two = SimpleNamespace(json=lambda: {"id": 23, "part_id": 31, "quantity": 1})
    found = SimpleNamespace(json=lambda: catalog.model_dump(mode="json"))
    empty = SimpleNamespace(json=lambda: {"vehicle_id": 8, "service_record_id": 12, "parts": []})
    replies = iter([one, found, two])
    def post(*args, **kwargs):
        result = next(replies)
        if result is one:
            committed[22] = "Synthetic manual snapshot"
        elif result is two:
            committed[23] = catalog.name
        return result
    client = SimpleNamespace(get=Mock(return_value=empty), post=Mock(side_effect=post))
    def manual_request(*args, **values):
        native._part_reservations.add((12, 8, 42, "Synthetic manual snapshot"))
        return ManualServicePartCreate(source="manual", name="Synthetic manual snapshot", **values)
    def catalog_request(*args):
        native._part_reservations.add((12, 8, 42, catalog.name))
        return CatalogServicePartCreate(source="catalog", preview=catalog)
    def assert_headers(response, *args):
        if response is (one if failed_write == "manual" else two):
            raise AssertionError("Synthetic header assertion after commit")
    monkeypatch.setattr(native_api, "parent_state", Mock(return_value="unchanged"))
    monkeypatch.setattr(native_api, "install", Mock())
    monkeypatch.setattr(native_api, "manual", manual_request)
    monkeypatch.setattr(native_api, "create_catalog", Mock(return_value=catalog))
    monkeypatch.setattr(native_api, "catalog_request", catalog_request)
    monkeypatch.setattr(native_api, "assert_headers", assert_headers)
    # Later DB verification is irrelevant to this regression; registration must
    # already have happened before the failing assertion can be reached.
    native.track_part_snapshot = Mock()
    with pytest.raises(AssertionError, match="header assertion after commit"):
        native_api.test_native_manual_catalog_list_confirmed_removal_and_service_link_protection(
            client, native, [first], (vehicle, record))
    expected = {22} if failed_write == "manual" else {22, 23}
    assert set(native._parts) == set(committed) == expected
    assert connect.call_count == 2  # Only the setup's mock guarded connections.

    def execute(sql, parameters):
        if sql.startswith("SELECT p.id FROM public.service_parts"):
            return Mock(fetchall=Mock(return_value=[(part_id,) for part_id, name in committed.items() if name == parameters[-1]]))
        assert sql.startswith("DELETE FROM public.service_parts")
        part_id, service_id, vehicle_id, user_id, name = parameters
        assert part_id in expected and (service_id, vehicle_id, user_id) == (12, 8, 42)
        assert committed.pop(part_id) == name
        return Mock()
    connection = Mock(execute=Mock(side_effect=execute))
    native._delete_linked_fixtures(connection)
    deleted = {call.args[1][0] for call in connection.execute.call_args_list if call.args[0].startswith("DELETE")}
    assert deleted == expected and committed == {}
