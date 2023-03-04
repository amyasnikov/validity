import logging

from dcim.models import Device
from django.http import Http404
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from validity.config_compliance.device_config import DeviceConfig
from validity.config_compliance.exceptions import DeviceConfigError
from validity.queries import DeviceQS


logger = logging.getLogger(__name__)


@register_model_view(Device, "serialized_config")
class DeviceSerializedConfigView(generic.ObjectView):
    template_name = "validity/device_config.html"
    tab = ViewTab("Serialized Config", permission="dcim.view_device")
    queryset = DeviceQS().annotate_json_repo().annotate_json_serializer()

    def get_object(self, **kwargs):
        it = self.queryset.filter(pk=self.kwargs["pk"]).json_iterator("repo", "serializer")
        try:
            self.object = next(it)
            return self.object
        except StopIteration:
            raise Http404

    def get_extra_context(self, request, instance):
        try:
            config = DeviceConfig.from_device(self.object)
            return {"config": config}
        except DeviceConfigError as e:
            logger.info("Cannot render serialized config, %s", e)
            return {"config": None}
