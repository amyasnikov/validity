from dcim.filtersets import DeviceFilterSet
from dcim.tables import DeviceTable
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables
from .base import TableMixin


class KeyBundleListView(generic.ObjectListView):
    queryset = models.KeyBundle.objects.all()
    table = tables.KeyBundleTable
    filterset = filtersets.KeyBundleFilterSet
    filterset_form = forms.KeyBundleFilterForm


@register_model_view(models.KeyBundle)
class KeyBundleView(TableMixin, generic.ObjectView):
    queryset = models.KeyBundle.objects.prefetch_related("tags")
    table = DeviceTable
    filterset = DeviceFilterSet
    object_table_field = "bound_devices"

    def get_extra_context(self, request, instance):
        return super().get_extra_context(request, instance) | {"format": request.GET.get("format", "yaml")}


@register_model_view(models.KeyBundle, "delete")
class KeyBundleDeleteView(generic.ObjectDeleteView):
    queryset = models.KeyBundle.objects.all()


class KeyBundleBulkDeleteView(generic.BulkDeleteView):
    queryset = models.KeyBundle.objects.all()
    filterset = filtersets.KeyBundleFilterSet
    table = tables.KeyBundleTable


@register_model_view(models.KeyBundle, "edit")
class KeyBundleEditView(generic.ObjectEditView):
    queryset = models.KeyBundle.objects.all()
    form = forms.KeyBundleForm
