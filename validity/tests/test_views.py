import textwrap

import factories
from base import ViewTest
from factories import (
    DeviceTypeFactory,
    GitRepoFactory,
    LocationFactory,
    ManufacturerFactory,
    PlatformFactory,
    SelectorFactory,
    SiteFactory,
    TagFactory,
    TestDBFactory,
)

from validity import models


class TestDBNameSet(ViewTest):
    factory_class = factories.NameSetDBFactory
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


class TestGitNameSet(ViewTest):
    factory_class = factories.NameSetGitFactory
    model_class = models.NameSet
    post_body = {
        "name": "nameset-1",
        "description": "descr",
        "_global": False,
        "tests": [TestDBFactory, TestDBFactory],
        "definitions": "",
        "repo": GitRepoFactory,
        "file_path": "some/file.txt",
    }


class TestGitRepo(ViewTest):
    factory_class = factories.GitRepoFactory
    model_class = models.GitRepo
    post_body = {
        "name": "repo-1",
        "git_url": "http://some.url/path",
        "web_url": "http://some.url/path",
        "device_config_path": "device/path",
        "default": True,
        "username": "admin",
        "password": "1234",
        "branch": "master",
    }


class TestReport(ViewTest):
    factory_class = factories.ReportFactory
    model_class = models.ComplianceReport
    get_suffixes = ["", "list"]
    post_suffixes = []
    post_body = {}


class TestSelector(ViewTest):
    factory_class = factories.SelectorFactory
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
        "dynamic_pairs": "NAME",
    }


class TestDBSerializer(ViewTest):
    factory_class = factories.SerializerDBFactory
    model_class = models.ConfigSerializer
    post_body = {"name": "serializer-1", "extraction_method": "TTP", "ttp_template": "interface {{interface}}"}


class TestGitSerializer(ViewTest):
    factory_class = factories.SerializerGitFactory
    model_class = models.ConfigSerializer
    post_body = {
        "name": "serializer-1",
        "extraction_method": "TTP",
        "ttp_template": "",
        "repo": GitRepoFactory,
        "file_path": "some_file.txt",
    }


class TestTestResult(ViewTest):
    get_suffixes = ["", "list"]
    post_suffixes = []
    factory_class = factories.TestResultFactory
    model_class = models.ComplianceTestResult
    post_body = {}


class TestDBTest(ViewTest):
    factory_class = factories.TestDBFactory
    model_class = models.ComplianceTest
    post_body = {
        "name": "test-1",
        "description": "some description",
        "severity": "HIGH",
        "expression": "1==1",
        "selectors": [SelectorFactory, SelectorFactory],
    }


class TestGitTest(ViewTest):
    factory_class = factories.TestDBFactory
    model_class = models.ComplianceTest
    post_body = {
        "name": "test-1",
        "description": "some description",
        "severity": "LOW",
        "expression": "",
        "selectors": [SelectorFactory],
        "repo": GitRepoFactory,
        "file_path": "some/file.txt",
    }
