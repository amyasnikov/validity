from dcim.filtersets import DeviceFilterSet
from dcim.models import Device, DeviceType, Manufacturer
from dcim.tables import DeviceTable
from django.db.models import Count, Q
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables
from .base import TableMixin


class SerializerListView(generic.ObjectListView):
    queryset = models.Serializer.objects.annotate(command_count=Count("commands"))
    table = tables.SerializerTable
    filterset = filtersets.SerializerFilterSet
    filterset_form = forms.SerializerFilterForm


@register_model_view(models.Serializer)
class SerializerView(TableMixin, generic.ObjectView):
    queryset = models.Serializer.objects.all()
    object_table_field = "bound_devices"
    table = DeviceTable
    filterset = DeviceFilterSet

    def get_extra_context(self, request, instance):
        cf_filter = Q(custom_field_data__serializer=instance.pk)
        related_models = [
            (model.objects.restrict(request.user, "view").filter(cf_filter), "cf_serializer")
            for model in (Device, DeviceType, Manufacturer)
        ]
        related_models.append(
            (models.Command.objects.restrict(request.user, "view").filter(serializer=instance), "serializer_id")
        )
        return super().get_extra_context(request, instance) | {"related_models": related_models}


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
