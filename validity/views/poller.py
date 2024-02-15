from dcim.filtersets import DeviceFilterSet
from dcim.tables import DeviceTable
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables
from validity.pollers.default_credentials import all_credentials
from .base import TableMixin


class PollerListView(generic.ObjectListView):
    queryset = models.Poller.objects.all()
    table = tables.PollerTable
    filterset = filtersets.PollerFilterSet
    filterset_form = forms.PollerFilterForm


@register_model_view(models.Poller)
class PollerView(TableMixin, generic.ObjectView):
    queryset = models.Poller.objects.prefetch_related("tags", "commands")
    table = DeviceTable
    filterset = DeviceFilterSet
    object_table_field = "bound_devices"

    def get_extra_context(self, request, instance):
        return super().get_extra_context(request, instance) | {"format": request.GET.get("format", "yaml")}


@register_model_view(models.Poller, "delete")
class PollerDeleteView(generic.ObjectDeleteView):
    queryset = models.Poller.objects.all()


class PollerBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Poller.objects.all()
    filterset = filtersets.PollerFilterSet
    table = tables.PollerTable


@register_model_view(models.Poller, "edit")
class PollerEditView(generic.ObjectEditView):
    queryset = models.Poller.objects.all()
    form = forms.PollerForm
    template_name = "validity/poller_edit.html"

    def get_extra_context(self, request, instance):
        return {"default_credentials": all_credentials}
