from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_tables2 import Column, Table
from netbox.tables import BooleanColumn as BooleanColumn
from netbox.tables import ChoiceFieldColumn, ManyToManyColumn, NetBoxTable

from validity import models
from .queries import count_devices_per_repo, count_devices_per_serializer


class SelectorTable(NetBoxTable):
    name = Column(linkify=True)
    filter_operation = ChoiceFieldColumn()
    name_filter = BooleanColumn(empty_values=())
    tag_filter = BooleanColumn(accessor="tag_filter__all")
    manufacturer_filter = BooleanColumn(accessor="manufacturer_filter__all")
    type_filter = BooleanColumn(accessor="type_filter__all")
    platform_filter = BooleanColumn(accessor="platform_filter__all")
    status_filter = BooleanColumn(empty_values=())
    location_filter = BooleanColumn(accessor="location_filter__all")
    site_filter = BooleanColumn(accessor="site_filter__all")
    dynamic_pairs = ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = models.ComplianceSelector
        fields = (
            "name",
            "filter_operation",
            "name_filter",
            "tag_filter",
            "manufacturer_filter",
            "type_filter",
            "platform_filter",
            "status_filter",
            "location_filter",
            "site_filter",
            "dynamic_pairs",
        )
        default_columns = fields


class ComplianceTestTable(NetBoxTable):
    name = Column(linkify=True)
    selectors = ManyToManyColumn(linkify_item=True)
    severity = ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = models.ComplianceTest
        fields = ("name", "severity", "selectors", "passed", "failed")
        default_columns = fields


class ComplianceResultTable(NetBoxTable):
    id = Column(linkify=True)
    test = Column(linkify=True)
    device = Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.ComplianceTestResult
        fields = ("id", "test", "device", "passed", "created")
        exclude = ("actions",)
        default_columns = fields


class GitRepoTable(NetBoxTable):
    name = Column(linkify=True)
    total_devices = Column(empty_values=())

    class Meta(NetBoxTable.Meta):
        model = models.GitRepo
        fields = ("name", "default", "total_devices")
        default_columns = fields

    def __init__(self, *args, extra_columns=None, **kwargs):
        super().__init__(*args, extra_columns=extra_columns, **kwargs)
        self.total_devices_map = count_devices_per_repo()

    def render_total_devices(self, record):
        return self.total_devices_map.get(record.id, 0)


class ConfigSerializerTable(NetBoxTable):
    name = Column(linkify=True)
    total_devices = Column(empty_values=())

    class Meta(NetBoxTable.Meta):
        model = models.ConfigSerializer
        fields = ("name", "total_devices")
        default_columns = fields

    def __init__(self, *args, extra_columns=None, **kwargs):
        super().__init__(*args, extra_columns=extra_columns, **kwargs)
        self.total_devices_map = count_devices_per_serializer()

    def render_total_devices(self, record):
        return self.total_devices_map.get(record.id, 0)


class ExplanationColumn(Column):
    def render(self, value):
        return format_html("<code>{}</code>", value)


class ExplanationTable(Table):
    left = ExplanationColumn(empty_values=(), verbose_name=_("Expression"))
    right = ExplanationColumn(empty_values=(), verbose_name=_("Value"))

    class Meta:
        template_name = "django_tables2/bootstrap.html"


class NameSetTable(NetBoxTable):
    name = Column(linkify=True)
    tests = ManyToManyColumn(linkify_item=True)

    class Meta(NetBoxTable.Meta):
        model = models.NameSet
        fields = ("name", "_global", "tests")
        default_columns = fields
