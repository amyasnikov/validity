from dcim.tables import DeviceTable
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables


class ConfigSerializerListView(generic.ObjectListView):
    queryset = models.ConfigSerializer.objects.all()
    table = tables.ConfigSerializerTable
    filterset = filtersets.ConfigSerializerFilterSet
    filterset_form = forms.ConfigSerializerFilterForm


@register_model_view(models.ConfigSerializer)
class ConfigSerializerView(generic.ObjectView):
    queryset = models.ConfigSerializer.objects.all()

    def get_extra_context(self, request, instance):
        table = DeviceTable(instance.bound_devices())
        table.configure(request)
        return {"device_table": table}


@register_model_view(models.ConfigSerializer, "delete")
class ConfigSerializerDeleteView(generic.ObjectDeleteView):
    queryset = models.ConfigSerializer.objects.all()


class ConfigSerializerBulkDeleteView(generic.BulkDeleteView):
    queryset = ConfigSerializerListView.queryset
    filterset = filtersets.ConfigSerializerFilterSet
    table = tables.ConfigSerializerTable


@register_model_view(models.ConfigSerializer, "edit")
class ConfigSerializerEditView(generic.ObjectEditView):
    queryset = models.ConfigSerializer.objects.all()
    form = forms.ConfigSerializerForm
