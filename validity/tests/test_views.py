import textwrap
from http import HTTPStatus

import pytest
from base import ViewTest
from factories import (
    CommandFactory,
    CompTestDBFactory,
    CompTestResultFactory,
    DataFileFactory,
    DataSourceFactory,
    DeviceFactory,
    DeviceTypeFactory,
    LocationFactory,
    ManufacturerFactory,
    NameSetDBFactory,
    NameSetDSFactory,
    PlatformFactory,
    PollerFactory,
    ReportFactory,
    SelectorFactory,
    SerializerDBFactory,
    SerializerDSFactory,
    SiteFactory,
    TagFactory,
    TenantFactory,
    state_item,
)

from validity import models
from validity.compliance.state import State


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
    get_suffixes = ["", "list", "delete"]
    post_suffixes = ["delete"]
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
    model_class = models.Serializer
    post_body = {"name": "serializer-1", "extraction_method": "TTP", "template": "interface {{interface}}"}


class TestDSSerializer(ViewTest):
    factory_class = SerializerDSFactory
    model_class = models.Serializer
    post_body = {
        "name": "serializer-1",
        "extraction_method": "TTP",
        "template": "",
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


@pytest.mark.parametrize("item", [None, "config", "show_ver", "bad_cmd", "non-existent"])
@pytest.mark.django_db
def test_get_serialized_state(admin_client, item, monkeypatch):
    device = DeviceFactory()
    state = State(
        {
            "config": state_item("config", {"vlans": [1, 2, 3]}),
            "show_ver": state_item("show_ver", {"version": "v1.2.3"}),
            "bad_cmd": state_item("bad_cmd", {}, data_file=None),
        }
    )
    monkeypatch.setattr(models.VDevice, "state", state)
    params = {"state_item": item} if item is not None else {}
    resp = admin_client.get(f"/dcim/devices/{device.pk}/serialized_state/", params)
    assert resp.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_report_devices(admin_client):
    report = ReportFactory(passed_results=4, failed_results=2)
    resp = admin_client.get(f"/plugins/validity/reports/{report.pk}/devices/")
    assert resp.status_code == HTTPStatus.OK


class TestPoller(ViewTest):
    factory_class = PollerFactory
    model_class = models.Poller
    post_body = {
        "name": "poller-1",
        "connection_type": "netmiko",
        "public_credentials": '{"username": "admin"}',
        "private_credentials": '{"password": "ADMIN"}',
        "commands": [CommandFactory, CommandFactory],
    }


class TestCommand(ViewTest):
    factory_class = CommandFactory
    model_class = models.Command
    post_body = {
        "name": "command-1",
        "label": "command_1",
        "type": "CLI",
        "cli_command": "show run",
    }


@pytest.mark.django_db
def test_datasource_devices(admin_client):
    data_source = DataSourceFactory(custom_field_data={"default": True})
    DeviceFactory()
    DeviceFactory()
    resp = admin_client.get(data_source.get_absolute_url() + "devices/")
    assert resp.status_code == HTTPStatus.OK
