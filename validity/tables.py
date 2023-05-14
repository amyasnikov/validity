from functools import partial

from dcim.models import Device
from dcim.tables import DeviceTable
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_tables2 import Column, RequestConfig, Table
from netbox.tables import BooleanColumn as BooleanColumn
from netbox.tables import ChoiceFieldColumn, ManyToManyColumn, NetBoxTable
from utilities.paginator import EnhancedPaginator

from validity import models
from validity.utils.misc import colorful_percentage


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
    tenant_filter = BooleanColumn(accessor="tenant_filter__all")
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
            "tenant_filter",
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
        self.total_devices_map = models.VDevice.objects.count_per_repo()

    def render_total_devices(self, record):
        return self.total_devices_map.get(record.id, 0)


class ConfigSerializerTable(NetBoxTable):
    name = Column(linkify=True)
    extraction_method = ChoiceFieldColumn()
    total_devices = Column(empty_values=())

    class Meta(NetBoxTable.Meta):
        model = models.ConfigSerializer
        fields = ("name", "extraction_method", "total_devices")
        default_columns = fields

    def __init__(self, *args, extra_columns=None, **kwargs):
        super().__init__(*args, extra_columns=extra_columns, **kwargs)
        self.total_devices_map = models.VDevice.objects.count_per_serializer()

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


class ComplianceReportTable(NetBoxTable):
    id = Column(linkify=True)
    groupby_value = Column(
        verbose_name=_("GroupBy Value"),
        linkify=lambda record: reverse(record["viewname"], kwargs={"pk": record["groupby_pk"]}),
        empty_values=(None,),
    )
    device_count = Column(verbose_name=_("Devices"), empty_values=())
    test_count = Column(verbose_name=_("Unique Tests"), empty_values=())
    total_stats = Column(verbose_name=_("Overall Passed"), empty_values=())
    low_stats = Column(verbose_name=_("Low Severity"), empty_values=())
    middle_stats = Column(verbose_name=_("Middle Severity"), empty_values=())
    high_stats = Column(verbose_name=_("High Severity"), empty_values=())

    class Meta(NetBoxTable.Meta):
        model = models.ComplianceReport
        fields = (
            "id",
            "groupby_value",
            "device_count",
            "test_count",
            "total_stats",
            "low_stats",
            "middle_stats",
            "high_stats",
            "created",
        )
        exclude = ("actions",)
        default_columns = fields

    def _render_stats(self, severity, record):
        def get_table_attr(obj, attr_name):
            return getattr(obj, attr_name) if hasattr(obj, attr_name) else obj.get(attr_name)

        count = get_table_attr(record, f"{severity}_count")
        if not count:
            return "—"
        passed = get_table_attr(record, f"{severity}_passed")
        percentage = get_table_attr(record, f"{severity}_percentage")
        return mark_safe(f"{passed}/{count} ") + colorful_percentage(percentage)

    def render_total_stats(self, record):
        return self._render_stats("total", record)

    def render_low_stats(self, record):
        return self._render_stats("low", record)

    def render_middle_stats(self, record):
        return self._render_stats("middle", record)

    def render_high_stats(self, record):
        return self._render_stats("high", record)


class DynamicPairsTable(DeviceTable):
    dynamic_pair = Column(verbose_name="Dynamic Pair", linkify=True)

    class Meta(DeviceTable.Meta):
        model = Device
        fields = DeviceTable.Meta.fields + ("dynamic_pair",)
        default_columns = DeviceTable.Meta.default_columns + ("dynamic_pair",)

    def get_paginate_by(self, request, max_paginate_by) -> int:
        try:
            per_page = int(request.GET["per_page"])
            if per_page > max_paginate_by:
                per_page = max_paginate_by
            return per_page
        except (KeyError, ValueError):
            return max_paginate_by // 2

    def configure(self, request, max_paginate_by=None, orphans=None):
        def get_page_lengths(self):
            return (max_paginate_by // 2, max_paginate_by)

        super().configure(request)
        if max_paginate_by and orphans:
            paginator_class = type("CustomPaginator", (EnhancedPaginator,), {"get_page_lengths": get_page_lengths})
            paginator_class = partial(paginator_class, orphans=orphans)
            paginate_by = self.get_paginate_by(request, max_paginate_by)
            paginate = {"paginator_class": paginator_class, "per_page": paginate_by}
            RequestConfig(request, paginate).configure(self)
