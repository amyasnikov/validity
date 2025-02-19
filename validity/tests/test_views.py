import textwrap
from functools import partial
from http import HTTPStatus
from typing import Callable
from unittest.mock import Mock

import pytest
from base import ViewTest
from django.urls import reverse
from django.utils.functional import classproperty
from factories import (
    BackupPointFactory,
    CommandFactory,
    CompTestDBFactory,
    CompTestResultFactory,
    DataFileFactory,
    DataSourceFactory,
    DeviceFactory,
    DeviceTypeFactory,
    DSBackupJobFactory,
    LocationFactory,
    ManufacturerFactory,
    NameSetDBFactory,
    NameSetDSFactory,
    PlatformFactory,
    PollerFactory,
    PollingDSFactory,
    ReportFactory,
    RunTestsJobFactory,
    SelectorFactory,
    SerializerDBFactory,
    SerializerDSFactory,
    SiteFactory,
    TagFactory,
    TenantFactory,
    state_item,
)

from validity import dependencies, models
from validity.compliance.state import State
from validity.scripts.data_models import RunTestsParams


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


@pytest.mark.parametrize("query_params", [{}, {"sort": "device"}, {"sort": "-device"}])
@pytest.mark.django_db
def test_report_devices(admin_client, query_params):
    report = ReportFactory(passed_results=4, failed_results=2)
    resp = admin_client.get(f"/plugins/validity/reports/{report.pk}/devices/", query_params)
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


class TestCustomCommand(ViewTest):
    factory_class = partial(CommandFactory, parameters={"a": {"b": {"c": "d"}}}, type="custom")
    model_class = models.Command
    post_body = {
        "name": "cmd-2",
        "label": "cmd_2",
        "type": "custom",
        "params": '{"p1": "v1"}',
    }
    get_suffixes: list[str] = ["", "add", "edit"]
    post_suffixes: list[str] = ["edit", "delete", "add"]

    @pytest.mark.django_db
    def test_params_are_saved_properly(self, admin_client):
        url = reverse("plugins:validity:command_add")
        resp = admin_client.post(url, self.post_body)
        assert resp.status_code == HTTPStatus.FOUND
        command = models.Command.objects.get()
        assert command.parameters == {"p1": "v1"}


class TestBackupPoint(ViewTest):
    factory_class = BackupPointFactory
    model_class = models.BackupPoint
    post_body = {
        "name": "bp",
        "data_source": PollingDSFactory,
        "backup_after_sync": True,
        "method": "S3",
        "url": "http://ex.com/qwer",
        "aws_access_key_id": "123",
        "aws_secret_access_key": "456",
        "archive": True,
    }

    @pytest.mark.parametrize("has_workers, status_code", [(True, HTTPStatus.FOUND), (False, HTTPStatus.OK)])
    @pytest.mark.django_db
    def test_backup_button(self, di, has_workers, status_code, admin_client):
        bp = BackupPointFactory()
        launcher = Mock(has_workers=has_workers, return_value=DSBackupJobFactory())
        with di.override({dependencies.backup_launcher: lambda: launcher}):
            resp = admin_client.post(bp.get_absolute_url())
            assert resp.status_code == status_code
            if resp.status_code == HTTPStatus.FOUND:
                launcher.assert_called_once()
                assert launcher.call_args.args[0].backuppoint_id == bp.pk


def test_datasource_with_extensions(admin_client, create_custom_fields):
    data_source = DataSourceFactory(type="device_polling")
    resp = admin_client.get(data_source.get_absolute_url())
    assert resp.status_code == HTTPStatus.OK
    assert b"Polling info" in resp.content
    assert b"Related Objects" in resp.content


@pytest.mark.django_db
def test_datasource_devices(admin_client):
    data_source = DataSourceFactory(custom_field_data={"default": True})
    DeviceFactory()
    DeviceFactory()
    resp = admin_client.get(data_source.get_absolute_url() + "devices/")
    assert resp.status_code == HTTPStatus.OK


class TestRunTests:
    url = "/plugins/validity/tests/run/"

    def test_get(self, admin_client):
        resp = admin_client.get(self.url)
        assert resp.status_code == HTTPStatus.OK

    @pytest.mark.parametrize(
        "form_data, status_code, has_workers",
        [
            ({}, HTTPStatus.FOUND, True),
            ({}, HTTPStatus.OK, False),
            ({"devices": [1, 2]}, HTTPStatus.OK, True),  # devices do not exist
        ],
    )
    def test_post(self, admin_client, di, form_data, status_code, has_workers):
        launcher = Mock(**{"has_workers": has_workers, "return_value.pk": 1})
        with di.override({dependencies.runtests_launcher: lambda: launcher}):
            result = admin_client.post(self.url, form_data)
            assert result.status_code == status_code
            if status_code == HTTPStatus.FOUND:  # if form is valid
                launcher.assert_called_once()
                assert isinstance(launcher.call_args.args[0], RunTestsParams)


@pytest.mark.parametrize("job_factory", [RunTestsJobFactory, DSBackupJobFactory])
def test_scriptresult(admin_client, job_factory):
    job = job_factory()
    resp = admin_client.get(f"/plugins/validity/scripts/results/{job.pk}/")
    assert resp.status_code == HTTPStatus.OK


#
# Test Bulk Import Views
#


class BulkImportViewTest(ViewTest):
    get_suffixes = ["import"]
    post_suffixes = ["import"]
    detail_suffixes = {}
    extra_factories: list[Callable[[], None]] = []
    base_body = {"import_method": "direct", "format": "auto", "csv_delimiter": "auto"}
    post_data: str

    @classmethod
    def create_models(cls):
        result = super().create_models()
        for factory in cls.extra_factories:
            factory()
        return result

    @classproperty
    def post_body(cls):
        return cls.base_body | {"data": cls.post_data}


class TestSelectorImportView(BulkImportViewTest):
    factory_class = SelectorFactory
    model_class = models.ComplianceSelector
    extra_factories = [
        partial(DeviceTypeFactory, slug="mod1"),
        partial(TenantFactory, slug="t1"),
        partial(TenantFactory, slug="t2"),
    ]
    post_data = 'name,filter_operation,type_filter,tenant_filter\nsel1,OR,mod1,"t1,t2"'


class TestNameSetImportView(BulkImportViewTest):
    factory_class = NameSetDBFactory
    model_class = models.NameSet
    post_data = (
        "name,description,global,definitions\n"
        '''ns1,some_description,true,"__all__=['defaultdict']\nfrom collections import defaultdict"'''
    )


class TestCompTestImportView(BulkImportViewTest):
    factory_class = CompTestDBFactory
    model_class = models.ComplianceTest
    post_data = "name,severity,description,selectors,data_source,data_file\n" "t1,LOW,some descr,s1,ds1,f1"
    extra_factories = [partial(SelectorFactory, name="s1"), partial(DataFileFactory, path="f1", source__name="ds1")]


class TestSerializerImportView(BulkImportViewTest):
    factory_class = SerializerDBFactory
    model_class = models.Serializer
    post_data = "name,extraction_method,parameters,template\n" 'ser1,TTP,{"jq_expression": ".data"},some_template_code'


class TestCommandImportView(BulkImportViewTest):
    factory_class = CommandFactory
    model_class = models.Command
    post_data = "name,label,type,parameters\n" 'c1,c1,CLI,{"cli_command": "show_run"}'


class TestPollerImportView(BulkImportViewTest):
    factory_class = PollerFactory
    model_class = models.Poller
    post_data = (
        "name,connection_type,commands,public_credentials,private_credentials\n"
        'p1,netmiko,"c1,c2",{"cred1": "va1"},{"cred2": "val2"}'
    )
    extra_factories = [partial(CommandFactory, label="c1"), partial(CommandFactory, label="c2")]


class TestBackupPointImportView(BulkImportViewTest):
    factory_class = BackupPointFactory
    model_class = models.BackupPoint
    post_data = (
        "name;data_source;backup_after_sync;method;url;parameters\n"
        'bp1;ds1;true;git;http://ex.com/qwe;{"username": "a", "password": "b"}'
    )
    extra_factories = [partial(DataSourceFactory, name="ds1", type="device_polling")]
