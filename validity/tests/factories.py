import factory
from dcim.models import DeviceRole, DeviceType, Location, Manufacturer, Platform, Site
from extras.models import Tag
from factory.django import DjangoModelFactory
from tenancy.models import Tenant

from validity import models


class GitRepoFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"repo-{n}")
    git_url = "http://some.url/repo"
    web_url = "http://some.url/repo/{{branch}}"
    device_config_path = "some/path/{{device.name}}.txt"
    username = ""

    class Meta:
        model = models.GitRepo

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.password = extracted
        self.save()


class GitRepoLinkFactory(DjangoModelFactory):
    repo = factory.SubFactory(GitRepoFactory)
    file_path = "some/file.txt"


class NameSetDBFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"nameset-{n}")
    _global = False
    definitions = "__all__ = ['f']\ndef f(): pass"

    class Meta:
        model = models.NameSet


class NameSetGitFactory(GitRepoLinkFactory, NameSetDBFactory):
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
    ttp_template = "interface {{ interface }}"

    class Meta:
        model = models.ConfigSerializer


class SerializerGitFactory(GitRepoLinkFactory, SerializerDBFactory):
    ttp_template = ""

    class Meta:
        model = models.ConfigSerializer


class CompTestDBFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"test-{n}")
    expression = "1==1"

    class Meta:
        model = models.ComplianceTest


class CompTestGitFactory(GitRepoLinkFactory, CompTestDBFactory):
    expression = ""

    class Meta:
        model = models.ComplianceTest


class ReportFactory(DjangoModelFactory):
    class Meta:
        model = models.ComplianceReport


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
