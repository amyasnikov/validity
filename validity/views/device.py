import logging

from dcim.models import Device
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from validity.config_compliance.exceptions import DeviceConfigError
from validity.models import VDevice
from .test_result import TestResultBaseView


logger = logging.getLogger(__name__)


@register_model_view(Device, "results")
class TestResultView(TestResultBaseView):
    parent_model = Device
    result_relation = "device"
    exclude_form_fields = ("platform_id", "tenant_id", "device_role_id", "manufacturer_id", "report_id", "selector_id")


@register_model_view(Device, "serialized_config")
class DeviceSerializedConfigView(generic.ObjectView):
    template_name = "validity/device_config.html"
    tab = ViewTab("Serialized Config", permission="dcim.view_device")
    queryset = VDevice.objects.all()

    def get_extra_context(self, request, instance):
        try:
            instance._meta = Device()._meta
            return {"config": instance.device_config, "format": request.GET.get("format", "yaml")}
        except DeviceConfigError as e:
            error = f"Cannot render serialized config, {e}"
            return {"error": error}
