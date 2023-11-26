import textwrap
from http import HTTPStatus

import pytest
from base import ViewTest
from factories import (
    CompTestDBFactory,
    CompTestResultFactory,
    ConfigFileFactory,
    DataFileFactory,
    DataSourceFactory,
    DeviceFactory,
    DeviceTypeFactory,
    LocationFactory,
    ManufacturerFactory,
    NameSetDBFactory,
    NameSetDSFactory,
    PlatformFactory,
    ReportFactory,
    SelectorFactory,
    SerializerDBFactory,
    SerializerDSFactory,
    SiteFactory,
    TagFactory,
    TenantFactory,
)

from validity import models


class TestDBNameSet(ViewTest):
    factory_class = NameSetDBFactory
    model_class = models.NameSet
    post_body = {
        "name": "nameset-1",
        "description": "descr",
        "_global": True,
        "definitions": textwrap.dedent(
            """
            __all__ = ['f']
            def f(): pass
        """
        ),
    }


class TestDSNameSet(ViewTest):
    factory_class = NameSetDSFactory
    model_class = models.NameSet
    post_body = {
        "name": "nameset-1",
        "description": "descr",
        "_global": False,
        "tests": [CompTestDBFactory, CompTestDBFactory],
        "definitions": "",
        "data_source": DataSourceFactory,
        "data_file": DataFileFactory,
    }


class TestReport(ViewTest):
    factory_class = ReportFactory
    model_class = models.ComplianceReport
    get_suffixes = ["", "list"]
    post_suffixes = []
    post_body = {}


class TestSelector(ViewTest):
    factory_class = SelectorFactory
    model_class = models.ComplianceSelector
    post_body = {
        "name": "sel-1",
        "filter_operation": "OR",
        "name_filter": "d([1-2])",
        "tag_filter": [TagFactory, TagFactory],
        "manufacturer_filter": [ManufacturerFactory, ManufacturerFactory],
        "type_filter": [DeviceTypeFactory, DeviceTypeFactory],
        "platform_filter": [PlatformFactory, PlatformFactory],
        "status_filter": "active",
        "location_filter": [LocationFactory],
        "site_filter": [SiteFactory],
        "tenant_filter": [TenantFactory],
        "dynamic_pairs": "NAME",
    }


class TestDBSerializer(ViewTest):
    factory_class = SerializerDBFactory
    model_class = models.ConfigSerializer
    post_body = {"name": "serializer-1", "extraction_method": "TTP", "ttp_template": "interface {{interface}}"}


class TestDSSerializer(ViewTest):
    factory_class = SerializerDSFactory
    model_class = models.ConfigSerializer
    post_body = {
        "name": "serializer-1",
        "extraction_method": "TTP",
        "ttp_template": "",
        "data_source": DataSourceFactory,
        "data_file": DataFileFactory,
    }


class TestTestResult(ViewTest):
    get_suffixes = ["", "list"]
    post_suffixes = []
    factory_class = CompTestResultFactory
    model_class = models.ComplianceTestResult
    post_body = {}


class TestDBTest(ViewTest):
    factory_class = CompTestDBFactory
    model_class = models.ComplianceTest
    post_body = {
        "name": "test-1",
        "description": "some description",
        "severity": "HIGH",
        "expression": "1==1",
        "selectors": [SelectorFactory, SelectorFactory],
    }


class TestDSTest(ViewTest):
    factory_class = CompTestDBFactory
    model_class = models.ComplianceTest
    post_body = {
        "name": "test-1",
        "description": "some description",
        "severity": "LOW",
        "expression": "",
        "selectors": [SelectorFactory],
        "data_source": DataSourceFactory,
        "data_file": DataFileFactory,
    }


@pytest.mark.django_db
def test_device_results(admin_client):
    device = DeviceFactory()
    ConfigFileFactory()
    serializer = SerializerDBFactory()
    device.custom_field_data["serializer"] = serializer.pk
    device.save()
    resp = admin_client.get(f"/dcim/devices/{device.pk}/serialized_config/")
    assert resp.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_report_devices(admin_client):
    report = ReportFactory(passed_results=4, failed_results=2)
    resp = admin_client.get(f"/plugins/validity/reports/{report.pk}/devices/")
    assert resp.status_code == HTTPStatus.OK
