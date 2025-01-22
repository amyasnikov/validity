from http import HTTPStatus
from unittest.mock import Mock

import pytest
from base import ApiGetTest, ApiPostGetTest
from factories import (
    BackupPointFactory,
    CommandFactory,
    CompTestDBFactory,
    CompTestResultFactory,
    DataFileFactory,
    DataSourceFactory,
    DeviceFactory,
    DeviceRoleFactory,
    DeviceTypeFactory,
    DSBackupJobFactory,
    LocationFactory,
    ManufacturerFactory,
    PlatformFactory,
    PollingDSFactory,
    ReportFactory,
    RunTestsJobFactory,
    SelectorFactory,
    SerializerDBFactory,
    SiteFactory,
    TagFactory,
    TenantFactory,
    state_item,
)

from validity import dependencies
from validity.models import VDevice
from validity.scripts import Launcher


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
        "role_factory": [DeviceRoleFactory],
        "platform_filter": [PlatformFactory, PlatformFactory],
        "status_filter": "active",
        "location_filter": [LocationFactory],
        "site_filter": [SiteFactory],
        "tenant_filter": [TenantFactory],
        "dynamic_pairs": "NAME",
    }


class TestDBSerializer(ApiPostGetTest):
    entity = "serializers"
    post_body = {"name": "serializer-1", "extraction_method": "TTP", "template": "interface {{interface}}"}

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


class TestSerializerParams(ApiPostGetTest):
    entity = "serializers"
    parameters = {"jq_expression": ".interface"}
    post_body = {
        "name": "serializer-1",
        "extraction_method": "TTP",
        "template": "interface {{interface}}",
        "parameters": parameters,
    }

    @pytest.mark.parametrize("params", [{"jq_expression": "(("}, {"unknown_param": 123}])
    def test_wrong_params(self, admin_client, params):
        body = self.post_body | {"parameters": params}
        resp = admin_client.post(self.url(), body, content_type="application/json")
        assert resp.status_code == HTTPStatus.BAD_REQUEST, resp.data


class TestSerializerWrongParams(ApiPostGetTest):
    entity = "serializers"
    parameters = {"jq_expression": ".interface"}
    post_body = {"name": "serializer-1", "extraction_method": "TTP", "template": "interface {{interface}}"}


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


class TestCommand(ApiPostGetTest):
    entity = "commands"
    post_body = {
        "name": "command-1",
        "label": "command_1",
        "type": "CLI",
        "serializer": SerializerDBFactory,
        "parameters": {"cli_command": "show version"},
    }


class TestPoller(ApiPostGetTest):
    entity = "pollers"
    post_body = {
        "name": "poller-1",
        "connection_type": "netmiko",
        "public_credentials": {"username": "admin"},
        "private_credentials": {"password": "1234"},
        "commands": [CommandFactory, CommandFactory],
    }


class TestBackupPoint(ApiPostGetTest):
    entity = "backup-points"
    post_body = {
        "name": "bp",
        "data_source": PollingDSFactory,
        "backup_after_sync": False,
        "method": "git",
        "upload_url": "http://ex.com/qwer",
        "parameters": {"username": "abc", "password": "123"},
    }

    @pytest.mark.django_db
    def test_backup(self, admin_client, di):
        bp = BackupPointFactory()
        url = self.url(bp.pk) + "backup/"
        launcher = Mock(spec=Launcher, return_value=DSBackupJobFactory())
        with di.override({dependencies.backup_launcher: lambda: launcher}):
            resp = admin_client.post(url)
            assert resp.status_code == HTTPStatus.OK
            assert resp.json()["result"]["id"] == launcher.return_value.pk
            launcher.assert_called_once()


@pytest.mark.parametrize("params", [{}, {"fields": ["name", "value"]}, {"name": ["config", "bad_cmd"]}])
@pytest.mark.django_db
def test_get_serialized_state(admin_client, params, monkeypatch):
    device = DeviceFactory()
    state = {
        "config": state_item("config", {"vlans": [1, 2, 3]}),
        "show_ver": state_item("show_ver", {"version": "v1.2.3"}),
        "bad_cmd": state_item("bad_cmd", {}, data_file=None),
    }
    monkeypatch.setattr(VDevice, "state", state)
    resp = admin_client.get(f"/api/dcim/devices/{device.pk}/serialized_state/", params)
    assert resp.status_code == HTTPStatus.OK
    answer = resp.json()
    expected_result_count = len(params.get("name", [])) or 3
    assert len(answer["results"]) == expected_result_count
    assert answer["count"] == expected_result_count
    for api_item in answer["results"]:
        if "fields" in params:
            assert api_item.keys() == set(params["fields"])
        assert state[api_item["name"]].serialized == api_item["value"]


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


@pytest.mark.parametrize(
    "post_body, status_code",
    [
        ({}, HTTPStatus.OK),
        ({"devices": [1, 2]}, HTTPStatus.BAD_REQUEST),  # devices do not exist
        ({"schedule_interval": 1, "sync_datasources": True, "explanation_verbosity": 2}, HTTPStatus.OK),
    ],
)
def test_run_tests(admin_client, di, post_body, status_code):
    launcher = Mock(return_value=RunTestsJobFactory())
    with di.override({dependencies.runtests_launcher: lambda: launcher}):
        resp = admin_client.post("/api/plugins/validity/tests/run/", post_body, content_type="application/json")
        assert resp.status_code == status_code
        if resp.status_code == HTTPStatus.OK:
            launcher.assert_called_once()


def test_api_schema_is_not_broken(admin_client):
    resp = admin_client.get("/api/schema/")
    assert resp.status_code == HTTPStatus.OK
