import logging

from dcim.models import Device
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from validity.forms import StateSelectForm
from validity.models import VDevice
from .base import TestResultBaseView


logger = logging.getLogger(__name__)


@register_model_view(Device, "results")
class TestResultView(TestResultBaseView):
    parent_model = Device
    result_relation = "device"
    exclude_form_fields = ("platform_id", "tenant_id", "device_role_id", "manufacturer_id", "report_id", "selector_id")


@register_model_view(Device, "serialized_state")
class DeviceSerializedStateView(generic.ObjectView):
    template_name = "validity/device_state.html"
    tab = ViewTab("Serialized State", permission="dcim.view_device")
    queryset = VDevice.objects.prefetch_datasource().prefetch_serializer().prefetch_poller()
    form_cls = StateSelectForm
    default_state_item = "config"

    def get_extra_context(self, request, instance):
        state_item_name = request.GET.get("state_item", self.default_state_item)
        state_item = instance.state.get_full_item(state_item_name)
        state_form = self.form_cls(
            state=instance.state, initial={"state_item": state_item.name} if state_item else None
        )
        instance._meta = Device()._meta
        context = {"state_item": state_item, "state_form": state_form, "format": request.GET.get("format", "yaml")}
        if state_item is None:
            context["error"] = f'"{state_item_name}" is not a member of {instance} state.'
        elif (error := state_item.error) is not None:
            context["error"] = f"Cannot render state item. {error}"
        return context
