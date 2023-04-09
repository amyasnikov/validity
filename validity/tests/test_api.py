from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock

import pytest
from base import ApiGetTest, ApiPostGetTest
from django.utils import timezone
from factories import (
    CompTestDBFactory,
    CompTestResultFactory,
    DeviceFactory,
    DeviceTypeFactory,
    GitRepoFactory,
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


class TestGitNameSet(ApiPostGetTest):
    entity = "namesets"
    post_body = {
        "name": "nameset-1",
        "description": "nameset description",
        "global": False,
        "tests": [CompTestDBFactory, CompTestDBFactory],
        "repo": GitRepoFactory,
        "file_path": "some/file.txt",
    }


class TestGitRepo(ApiPostGetTest):
    entity = "git-repositories"
    post_body = {
        "name": "repo-1",
        "git_url": "http://some.url/path",
        "web_url": "http://some.url/webpath",
        "device_config_path": "some/path/{{device.name}}.txt",
        "default": True,
        "username": "admin",
        "password": "1234",
        "branch": "main",
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


class TestGitSerializer(ApiPostGetTest):
    entity = "serializers"
    post_body = {
        "name": "serializer-1",
        "extraction_method": "TTP",
        "repo": GitRepoFactory,
        "file_path": "some_file.txt",
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


class TestGitTest(ApiPostGetTest):
    entity = "tests"
    post_body = {
        "name": "test-1",
        "description": "some description",
        "severity": "LOW",
        "selectors": [SelectorFactory],
        "repo": GitRepoFactory,
        "file_path": "some/file.txt",
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
    device.repo = GitRepoFactory(web_url="http://github.com/reponame")
    device.serializer = SerializerDBFactory()
    lm = timezone.now()
    config = DeviceConfig(
        device=device, config_path=Path("some/file.txt"), last_modified=lm, serialized={"key1": "value1"}
    )
    monkeypatch.setattr(DeviceConfig, "from_device", Mock(return_value=config))
    resp = admin_client.get(f"/api/dcim/devices/{device.pk}/serialized_config/")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json().keys() == {
        "serializer",
        "repo",
        "local_copy_last_updated",
        "config_web_link",
        "serialized_config",
    }
    assert resp.json()["serialized_config"] == {"key1": "value1"}
    assert resp.json()["local_copy_last_updated"] == lm.isoformat().replace("+00:00", "Z")
