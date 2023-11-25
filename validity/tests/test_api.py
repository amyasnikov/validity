from http import HTTPStatus
from unittest.mock import Mock

import pytest
from base import ApiGetTest, ApiPostGetTest
from django.utils import timezone
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
    PlatformFactory,
    ReportFactory,
    SelectorFactory,
    SerializerDBFactory,
    SiteFactory,
    TagFactory,
    TenantFactory,
)

from validity.config_compliance.device_config import DeviceConfig


class TestDBNameSet(ApiPostGetTest):
    entity = "namesets"
    post_body = {
        "name": "nameset-1",
        "description": "nameset description",
        "global": True,
        "definitions": "__all__ = ['f']\ndef f(): pass",
    }

    def get_extra_checks(self, resp_json, pk):
        if pk:
            assert resp_json["effective_definitions"]


class TestDSNameSet(ApiPostGetTest):
    entity = "namesets"
    post_body = {
        "name": "nameset-1",
        "description": "nameset description",
        "global": False,
        "tests": [CompTestDBFactory, CompTestDBFactory],
        "data_source": DataSourceFactory,
        "data_file": DataFileFactory,
    }


class TestSelector(ApiPostGetTest):
    entity = "selectors"
    post_body = {
        "name": "selector-1",
        "filter_operation": "OR",
        "name_filter": "device([0-9])",
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


class TestDBSerializer(ApiPostGetTest):
    entity = "serializers"
    post_body = {"name": "serializer-1", "extraction_method": "TTP", "ttp_template": "interface {{interface}}"}

    def get_extra_checks(self, resp_json, pk):
        if pk:
            assert resp_json["effective_template"]


class TestDSSerializer(ApiPostGetTest):
    entity = "serializers"
    post_body = {
        "name": "serializer-1",
        "extraction_method": "TTP",
        "data_source": DataSourceFactory,
        "data_file": DataFileFactory,
    }


class TestDBTest(ApiPostGetTest):
    entity = "tests"
    post_body = {
        "name": "test-1",
        "description": "some description",
        "severity": "HIGH",
        "expression": "1==1",
        "selectors": [SelectorFactory, SelectorFactory],
    }

    def get_extra_checks(self, resp_json, pk):
        if pk:
            assert resp_json["effective_expression"]


class TestDSTest(ApiPostGetTest):
    entity = "tests"
    post_body = {
        "name": "test-1",
        "description": "some description",
        "severity": "LOW",
        "selectors": [SelectorFactory],
        "data_source": DataSourceFactory,
        "data_file": DataFileFactory,
    }


class TestTestResult(ApiGetTest):
    factory = CompTestResultFactory
    entity = "test-results"


class TestReport(ApiGetTest):
    factory = ReportFactory
    entity = "reports"


@pytest.mark.django_db
def test_get_serialized_config(monkeypatch, admin_client):
    device = DeviceFactory()
    config_file = ConfigFileFactory()
    device.custom_field_data["serializer"] = SerializerDBFactory().pk
    device.save()
    device.data_source = config_file.source
    lm = timezone.now()
    config = DeviceConfig(device=device, plain_config="", last_modified=lm, serialized={"key1": "value1"})
    monkeypatch.setattr(DeviceConfig, "from_device", Mock(return_value=config))
    resp = admin_client.get(f"/api/dcim/devices/{device.pk}/serialized_config/")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json().keys() == {
        "data_source",
        "data_file",
        "local_copy_last_updated",
        "config_web_link",
        "serialized_config",
    }
    assert resp.json()["serialized_config"] == {"key1": "value1"}
    assert resp.json()["local_copy_last_updated"] == lm.isoformat().replace("+00:00", "Z")


@pytest.mark.django_db
def test_report_devices(admin_client):
    report = ReportFactory(passed_results=2, failed_results=1)
    resp = admin_client.get(f"/api/plugins/validity/reports/{report.pk}/devices/")
    assert resp.status_code == HTTPStatus.OK
    results = resp.json()["results"]
    assert len(results) == 3
    for device in results:
        assert len(device["results"]) == 1
        assert device["results_count"] == 1
