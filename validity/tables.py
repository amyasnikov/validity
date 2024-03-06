import itertools
from functools import partial

from dcim.models import Device
from dcim.tables import DeviceTable
from dcim.tables.template_code import DEVICE_LINK
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_tables2 import Column, RequestConfig, Table, TemplateColumn
from netbox.tables import BooleanColumn as BooleanColumn
from netbox.tables import ChoiceFieldColumn, ManyToManyColumn, NetBoxTable
from netbox.tables.columns import ActionsColumn, LinkedCountColumn
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
    passed = BooleanColumn()

    class Meta(NetBoxTable.Meta):
        model = models.ComplianceTestResult
        fields = ("id", "test", "device", "passed", "created")
        exclude = ("actions",)
        default_columns = fields


class TotalDevicesMixin(NetBoxTable):
    total_devices = Column(empty_values=())

    count_per: str

    def __init__(self, *args, extra_columns=None, **kwargs):
        super().__init__(*args, extra_columns=extra_columns, **kwargs)
        self.total_devices_map = getattr(models.VDevice.objects, f"count_per_{self.count_per}")()

    def render_total_devices(self, record):
        return self.total_devices_map.get(record.id, 0)


class SerializerTable(TotalDevicesMixin, NetBoxTable):
    name = Column(linkify=True)
    extraction_method = ChoiceFieldColumn()
    command_count = LinkedCountColumn(
        verbose_name=_("Commands"), viewname="plugins:validity:command_list", url_params={"serializer_id": "pk"}
    )

    count_per = "serializer"

    class Meta(NetBoxTable.Meta):
        model = models.Serializer
        fields = ("name", "extraction_method", "total_devices", "command_count")
        default_columns = fields


class PollerTable(TotalDevicesMixin, NetBoxTable):
    name = Column(linkify=True)
    connection_type = ChoiceFieldColumn()

    count_per = "poller"

    class Meta(NetBoxTable.Meta):
        model = models.Poller
        fields = ("name", "connection_type", "total_devices")
        default_columns = fields


class CommandTable(NetBoxTable):
    name = Column(linkify=True)
    type = ChoiceFieldColumn()
    serializer = Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.Command
        fields = ("name", "type", "retrieves_config", "serializer", "label")


class ExplanationColumn(Column):
    def render(self, value):
        return format_html('<code class="language-python">{}</code>', value)


class ExplanationTable(Table):
    counter = Column(verbose_name="#", empty_values=(), orderable=False)
    left = ExplanationColumn(empty_values=(), verbose_name=_("Expression"))
    right = ExplanationColumn(empty_values=(), verbose_name=_("Value"))

    def render_counter(self):
        self.row_counter = getattr(self, "row_counter", itertools.count(start=1))
        return format_html('<b class="mr-5">{}</b>', next(self.row_counter))

    class Meta:
        template_name = "django_tables2/bootstrap.html"


class NameSetTable(NetBoxTable):
    name = Column(linkify=True)
    tests = ManyToManyColumn(linkify_item=True)
    _global = BooleanColumn()

    class Meta(NetBoxTable.Meta):
        model = models.NameSet
        fields = ("name", "_global", "tests")
        default_columns = fields


class StatsColumn(Column):
    def __init__(self, data_prefix: str, **kwargs):
        super().__init__(**kwargs)
        self.data_prefix = data_prefix

    def render(self, value, record):
        def get_table_attr(obj, attr_name):
            return getattr(obj, attr_name) if hasattr(obj, attr_name) else obj.get(attr_name)

        count = get_table_attr(record, f"{self.data_prefix}_count")
        if not count:
            return "—"
        passed = get_table_attr(record, f"{self.data_prefix}_passed")
        percentage = get_table_attr(record, f"{self.data_prefix}_percentage")
        return mark_safe(f"{passed}/{count} ") + colorful_percentage(percentage)


class ComplianceReportTable(NetBoxTable):
    id = Column(linkify=True)
    groupby_value = Column(
        verbose_name=_("GroupBy Value"),
        linkify=lambda record: reverse(record["viewname"], kwargs={"pk": record["groupby_pk"]}),
        empty_values=(None,),
    )
    device_count = Column(verbose_name=_("Devices"), empty_values=())
    test_count = Column(verbose_name=_("Unique Tests"), empty_values=())
    total_stats = StatsColumn(data_prefix="total", verbose_name=_("Overall Passed"), empty_values=())
    low_stats = StatsColumn(data_prefix="low", verbose_name=_("Low Severity"), empty_values=())
    middle_stats = StatsColumn(data_prefix="middle", verbose_name=_("Middle Severity"), empty_values=())
    high_stats = StatsColumn(data_prefix="high", verbose_name=_("High Severity"), empty_values=())
    actions = ActionsColumn(actions=("delete",))

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
        default_columns = fields


class DeviceReportM2MColumn(ManyToManyColumn):
    def __init__(self, *args, badge_color: str = "", **kwargs):
        if badge_color:
            kwargs["attrs"] = kwargs.get("attrs", {}) | {
                "a": {"class": f"mb-1 badge rounded-pill text-{badge_color} border border-{badge_color}"}
            }
            kwargs["separator"] = " "
        kwargs.setdefault("transform", lambda obj: str(obj.test))
        super().__init__(*args, **kwargs)

    def render(self, value):
        """
        Default implementation does not draw "-" when all the results are filtered out
        """
        result = super().render(value)
        return result if result else "—"


class ComplianceReportDeviceTable(NetBoxTable):
    device = TemplateColumn(
        order_by=("_name",), template_code=DEVICE_LINK, linkify=True, accessor="name", attrs={"th": {"class": "col-2"}}
    )
    compliance_passed = BooleanColumn(
        verbose_name=_("Compliance Passed"),
        empty_values=(),
    )
    result_stats = StatsColumn(data_prefix="results", empty_values=(), verbose_name=_("Result Statistics"))
    passed_results = DeviceReportM2MColumn(
        linkify_item=True,
        verbose_name=_("Passed Tests"),
        filter=lambda qs: (obj for obj in qs.all() if obj.passed),
        accessor="results",
        badge_color="success",
    )
    failed_results = DeviceReportM2MColumn(
        linkify_item=True,
        verbose_name=_("Failed Tests"),
        filter=lambda qs: (obj for obj in qs.all() if not obj.passed),
        accessor="results",
        badge_color="danger",
    )

    class Meta(NetBoxTable.Meta):
        model = models.VDevice
        fields = ("device", "compliance_passed", "result_stats", "passed_results", "failed_results")
        default_columns = fields
        exclude = ("actions",)


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
