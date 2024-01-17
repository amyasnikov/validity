import datetime

import django
import factory
from dcim.models import DeviceRole, DeviceType, Location, Manufacturer, Platform, Site
from extras.models import Tag
from factory.django import DjangoModelFactory
from tenancy.models import Tenant

from validity import models
from validity.compliance.state import StateItem


DJANGO_MAJOR_VERSION = django.VERSION[:2]


class DataSourceFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"datasource-{n}")
    type = "local"
    source_url = "file:///some_path"

    class Meta:
        model = models.VDataSource


class DataFileFactory(DjangoModelFactory):
    source = factory.SubFactory(DataSourceFactory)
    path = factory.Sequence(lambda n: f"file-{n}.txt")
    data = "some contents".encode()
    size = len(data)
    last_updated = datetime.datetime.utcnow()
    hash = "1" * 64

    class Meta:
        model = models.VDataFile

    @factory.post_generation
    def to_memoryview(self, *args, **kwargs):
        if DJANGO_MAJOR_VERSION < (4, 2) and isinstance(self.data, bytes):
            self.data = memoryview(self.data)


class DataSourceLinkFactory(DjangoModelFactory):
    data_source = factory.SubFactory(DataSourceFactory)
    data_file = factory.SubFactory(DataFileFactory, source=data_source, data=factory.SelfAttribute("..contents_bin"))

    class Params:
        contents = "some_contents"
        contents_bin = factory.LazyAttribute(lambda o: o.contents.encode())


class NameSetDBFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"nameset-{n}")
    _global = False
    definitions = "__all__ = ['f']\ndef f(): pass"

    class Meta:
        model = models.NameSet


class NameSetDSFactory(DataSourceLinkFactory, NameSetDBFactory):
    definitions = ""

    class Meta:
        model = models.NameSet


class SelectorFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"selector-{n}")
    filter_operation = "AND"
    name_filter = ""
    dynamic_pairs = "NO"

    class Meta:
        model = models.ComplianceSelector


class SerializerDBFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"serializer-{n}")
    extraction_method = "TTP"
    template = "interface {{ interface }}"

    class Meta:
        model = models.Serializer


class SerializerDSFactory(DataSourceLinkFactory, SerializerDBFactory):
    template = ""

    class Meta:
        model = models.Serializer


class CompTestDBFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"test-{n}")
    expression = "1==1"

    class Meta:
        model = models.ComplianceTest


class CompTestDSFactory(DataSourceLinkFactory, CompTestDBFactory):
    expression = ""

    class Meta:
        model = models.ComplianceTest


class ReportFactory(DjangoModelFactory):
    class Meta:
        model = models.ComplianceReport

    @factory.post_generation
    def passed_results(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for _ in range(extracted):
            CompTestResultFactory(report=self, passed=True)

    @factory.post_generation
    def failed_results(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for _ in range(extracted):
            CompTestResultFactory(report=self, passed=False)


class ManufacturerFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"manufacturer-{n}")
    slug = factory.Sequence(lambda n: f"manufacturer-{n}")

    class Meta:
        model = Manufacturer


class DeviceTypeFactory(DjangoModelFactory):
    model = factory.Sequence(lambda n: f"model-{n}")
    manufacturer = factory.SubFactory(ManufacturerFactory)
    slug = factory.Sequence(lambda n: f"model-{n}")

    class Meta:
        model = DeviceType


class DeviceRoleFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"role-{n}")
    slug = factory.Sequence(lambda n: f"role-{n}")

    class Meta:
        model = DeviceRole


class SiteFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"site-{n}")
    slug = factory.Sequence(lambda n: f"site-{n}")

    class Meta:
        model = Site


class TenantFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"tenant-{n}")
    slug = factory.Sequence(lambda n: f"tenant-{n}")

    class Meta:
        model = Tenant


class DeviceFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"device-{n}")
    site = factory.SubFactory(SiteFactory)
    device_type = factory.SubFactory(DeviceTypeFactory)
    device_role = factory.SubFactory(DeviceRoleFactory)

    class Meta:
        model = models.VDevice


class TagFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"tag-{n}")
    slug = factory.Sequence(lambda n: f"tag-{n}")

    class Meta:
        model = Tag


class PlatformFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"platform-{n}")
    slug = factory.Sequence(lambda n: f"platform-{n}")

    class Meta:
        model = Platform


class LocationFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"location-{n}")
    slug = factory.Sequence(lambda n: f"location-{n}")
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Location


class CompTestResultFactory(DjangoModelFactory):
    test = factory.SubFactory(CompTestDBFactory)
    device = factory.SubFactory(DeviceFactory)
    dynamic_pair = factory.SubFactory(DeviceFactory)
    report = factory.SubFactory(ReportFactory)
    passed = True
    explanation = [("qwe", "rty")]

    class Meta:
        model = models.ComplianceTestResult


class CommandFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"command-{n}")
    label = factory.Sequence(lambda n: f"command_{n}")
    type = "CLI"
    parameters = {"cli_command": "show run"}

    class Meta:
        model = models.Command


class PollerFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"poller-{n}")
    connection_type = "netmiko"

    class Meta:
        model = models.Poller


_NOT_DEFINED = object()


def state_item(name, serialized, data_file=_NOT_DEFINED, command=_NOT_DEFINED):
    if data_file == _NOT_DEFINED:
        data_file = DataFileFactory()
    if command == _NOT_DEFINED:
        command = CommandFactory()
    command.label = name
    serializer = SerializerDBFactory()
    item = StateItem(serializer, data_file, command)
    item.__dict__["serialized"] = serialized
    return item
