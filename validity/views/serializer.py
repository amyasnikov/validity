from dcim.filtersets import DeviceFilterSet
from dcim.tables import DeviceTable
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables
from .base import TableMixin


class SerializerListView(generic.ObjectListView):
    queryset = models.Serializer.objects.all()
    table = tables.SerializerTable
    filterset = filtersets.SerializerFilterSet
    filterset_form = forms.SerializerFilterForm


@register_model_view(models.Serializer)
class SerializerView(TableMixin, generic.ObjectView):
    queryset = models.Serializer.objects.all()
    object_table_field = "bound_devices"
    table = DeviceTable
    filterset = DeviceFilterSet


@register_model_view(models.Serializer, "delete")
class SerializerDeleteView(generic.ObjectDeleteView):
    queryset = models.Serializer.objects.all()


class SerializerBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Serializer.objects.all()
    filterset = filtersets.SerializerFilterSet
    table = tables.SerializerTable


@register_model_view(models.Serializer, "edit")
class SerializerEditView(generic.ObjectEditView):
    queryset = models.Serializer.objects.all()
    form = forms.SerializerForm
