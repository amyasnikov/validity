from dcim.filtersets import DeviceFilterSet
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables
from .base import TableMixin


class ComplianceSelectorListView(generic.ObjectListView):
    queryset = models.ComplianceSelector.objects.all()
    table = tables.SelectorTable
    filterset = filtersets.ComplianceSelectorFilterSet
    filterset_form = forms.ComplianceSelectorFilterForm


@register_model_view(models.ComplianceSelector)
class ComplianceSelectorView(TableMixin, generic.ObjectView):
    queryset = models.ComplianceSelector.objects.prefetch_related(
        "tag_filter",
        "manufacturer_filter",
        "type_filter",
        "platform_filter",
        "location_filter",
        "site_filter",
        "tenant_filter",
        "tags",
    )
    filterset = DeviceFilterSet
    object_table_field = "devices"
    table = tables.DynamicPairsTable
    max_paginate_by = 10
    page_orphans = 1

    def configure_table(self, request, table, instance):
        if instance.dynamic_pairs == "NO":
            table.exclude += ("dynamic_pair",)
        table.configure(request, max_paginate_by=self.max_paginate_by, orphans=self.page_orphans)


@register_model_view(models.ComplianceSelector, "delete")
class ComplianceSelectorDeleteView(generic.ObjectDeleteView):
    queryset = models.ComplianceSelector.objects.all()


class ComplianceSelectorBulkDeleteView(generic.BulkDeleteView):
    queryset = models.ComplianceSelector.objects.all()
    filterset = filtersets.ComplianceSelectorFilterSet
    table = tables.SelectorTable


@register_model_view(models.ComplianceSelector, "edit")
class ComplianceSelectorEditView(generic.ObjectEditView):
    queryset = models.ComplianceSelector.objects.all()
    form = forms.ComplianceSelectorForm
