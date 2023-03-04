from dcim.models import Device
from django.db.models import BigIntegerField, Count, F
from django.db.models.functions import Cast
from netbox.views import generic
from dcim.tables import DeviceTable
from validity import models, tables, filtersets, forms
from utilities.views import register_model_view


class ConfigSerializerListView(generic.ObjectListView):
    queryset = models.ConfigSerializer.objects.annotate(
        total_devices=Count(
            Device.objects.annotate(szr=Cast("custom_field_data__config_serializer", BigIntegerField()))
            .filter(szr=F("id"))
            .values("id")
        )
    )
    table = tables.ConfigSerializerTable
    filterset = filtersets.ConfigSerializerFilterSet


@register_model_view(models.ConfigSerializer)
class ConfigSerializerView(generic.ObjectView):
    queryset = models.ConfigSerializer.objects.all()

    def get_extra_context(self, request, instance):
        table = DeviceTable(instance.devices())
        table.configure(request)
        return {'device_table': table}


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