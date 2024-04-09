from functools import cached_property

from core.models import DataSource
from dcim.filtersets import DeviceFilterSet
from dcim.tables import DeviceTable
from django.shortcuts import get_object_or_404
from django_tables2 import SingleTableMixin
from utilities.views import ViewTab, register_model_view

from validity.forms import DataSourceDevicesFilterForm
from validity.models import VDataSource
from validity.utils.orm import model_to_proxy
from .base import FilterViewWithForm


@register_model_view(DataSource, "devices")
class DataSourceBoundDevicesView(SingleTableMixin, FilterViewWithForm):
    template_name = "validity/aux_tab_table.html"
    tab = ViewTab("Bound Devices", badge=lambda obj: model_to_proxy(obj, VDataSource).bound_devices.count())
    model = DataSource
    filterset_class = DeviceFilterSet
    filterform_class = DataSourceDevicesFilterForm
    table_class = DeviceTable
    permission_required = "dcim.view_device"

    def get_queryset(self):
        return model_to_proxy(self.object, VDataSource).bound_devices

    @cached_property
    def object(self):
        return get_object_or_404(DataSource, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"object": self.object, "tab": self.tab}
