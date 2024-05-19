from itertools import product
from unittest.mock import Mock

import pytest
from factories import CommandFactory, CompTestDBFactory, DataSourceFactory, DeviceFactory

from validity.models import Command, ComplianceReport, ComplianceTestResult, VDevice


@pytest.mark.parametrize("store_results", [3, 2, 1])
@pytest.mark.django_db
def test_delete_old_results(store_results):
    report = ComplianceReport.objects.create()
    device1 = DeviceFactory()
    device2 = DeviceFactory()
    test1 = CompTestDBFactory()
    test2 = CompTestDBFactory()
    report_results = [
        ComplianceTestResult.objects.create(passed=True, device=device1, test=test1, explanation=[], report=report).pk,
        ComplianceTestResult.objects.create(passed=True, device=device2, test=test2, explanation=[], report=report).pk,
    ]
    result_per_devtest = 5
    for test, device in product([test1, test2], [device1, device2]):
        for i in range(result_per_devtest):
            ComplianceTestResult.objects.create(passed=True, device=device, test=test, explanation=i)

    assert ComplianceTestResult.objects.count() == 4 * result_per_devtest + len(report_results)
    ComplianceTestResult.objects.delete_old(_settings=Mock(store_last_results=store_results))
    assert ComplianceTestResult.objects.count() == 4 * store_results + len(report_results)
    assert ComplianceTestResult.objects.filter(pk__in=report_results).count() == len(report_results)
    for test, device in product([test1, test2], [device1, device2]):
        assert [
            *ComplianceTestResult.objects.filter(report=None, test=test, device=device)
            .order_by("created")
            .values_list("explanation", flat=True)
        ] == [*range(result_per_devtest - store_results, result_per_devtest)]


@pytest.mark.parametrize("store_reports", [3, 2, 1])
@pytest.mark.django_db
def test_delete_old_reports(store_reports):
    reports = [ComplianceReport.objects.create() for _ in range(10)]
    ComplianceReport.objects.delete_old(_settings=Mock(store_reports=store_reports))
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
