from dcim.tables import DeviceTable
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables


class ComplianceSelectorListView(generic.ObjectListView):
    queryset = models.ComplianceSelector.objects.all()
    table = tables.SelectorTable
    filterset = filtersets.ComplianceSelectorFilterSet
    filterset_form = forms.ComplianceSelectorFilterForm


@register_model_view(models.ComplianceSelector)
class ComplianceSelectorView(generic.ObjectView):
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

    def get_extra_context(self, request, instance):
        table = DeviceTable(instance.devices.all())
        table.configure(request)
        return {"device_table": table}


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
