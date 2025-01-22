from unittest.mock import Mock

import pytest
from factories import CommandFactory, DataSourceFactory, DeviceFactory

from validity.dependencies import validity_settings
from validity.managers import ComplianceSelectorQS
from validity.models import Command, ComplianceReport, ComplianceSelector, VDevice
from validity.settings import ValiditySettings


@pytest.mark.parametrize("store_reports", [3, 2, 1])
@pytest.mark.django_db
def test_delete_old_reports(store_reports, di):
    reports = [ComplianceReport.objects.create() for _ in range(10)]
    settings = ValiditySettings(store_reports=store_reports)
    with di.override({validity_settings: lambda: settings}):
        ComplianceReport.objects.delete_old()
        assert list(ComplianceReport.objects.order_by("created")) == reports[-store_reports:]


@pytest.mark.django_db
def test_set_file_paths(create_custom_fields):
    CommandFactory(label="cmd1")
    CommandFactory(label="cmd2")
    device = DeviceFactory(name="d1")
    ds = DataSourceFactory(
        name="ds1", custom_field_data={"device_command_path": "path/{{device.name}}/{{command.label}}"}
    )
    commands = Command.objects.set_file_paths(device=device, data_source=ds)
    for cmd in commands:
        assert cmd.path == f"path/d1/{cmd.label}"


@pytest.mark.django_db
def test_set_attribute():
    DeviceFactory(name="d1")
    DeviceFactory(name="d2")
    DeviceFactory(name="_d3")
    device_qs = VDevice.objects.all().set_attribute("attr1", "val1").set_attribute("attr2", "val2")
    for device in device_qs:
        assert device.attr1 == "val1" and device.attr2 == "val2"
    for device in device_qs.filter(name__startswith="d"):
        assert device.attr1 == "val1" and device.attr2 == "val2"


def test_prefetch_filters(monkeypatch):
    monkeypatch.setattr(ComplianceSelectorQS, "prefetch_related", Mock())
    ComplianceSelector.objects.all().prefetch_filters()
    ComplianceSelectorQS.prefetch_related.assert_called_once()
    assert set(ComplianceSelectorQS.prefetch_related.call_args.args) == {
        "tag_filter",
        "manufacturer_filter",
        "type_filter",
        "role_filter",
        "platform_filter",
        "location_filter",
        "site_filter",
        "tenant_filter",
    }
