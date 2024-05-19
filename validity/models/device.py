from functools import cached_property
from typing import TYPE_CHECKING, Optional

from dcim.models import Device

from validity.compliance.serialization import Serializable
from validity.compliance.state import State
from validity.managers import VDeviceQS
from .data import VDataSource


if TYPE_CHECKING:
    from .selector import ComplianceSelector


class VDevice(Device):
    objects = VDeviceQS.as_manager()
    data_source: VDataSource
    selector: Optional["ComplianceSelector"]
    prefer_ipv4: bool | None = None

    class Meta:
        proxy = True

    def _config_item(self) -> Serializable:
        """
        Serializable from  "device_config_path" file
        """
        try:
            config_path = self.data_source.get_config_path(self)
            data_file = self.data_source.datafiles.filter(path=config_path).first()
            return Serializable(self.serializer, data_file=data_file)
        except AttributeError as exc:
            if exc.obj is not None:
                raise
            return Serializable(self.serializer, data_file=None)

    @property
    def config(self) -> dict | list | None:
        return self.state.config

    @cached_property
    def state(self):
        try:
            commands = (
                self.poller.commands.select_related("serializer")
                .set_file_paths(self, self.data_source)
                .custom_postfetch(
                    "data_file", self.data_source.datafiles.all(), pk_field="path", remote_pk_field="path"
                )
            )
        except AttributeError:
            # if device has no poller or data_source
            commands = []
        return State.from_commands(commands).with_config(self._config_item())

    @cached_property
    def dynamic_pair(self) -> Optional["VDevice"]:
        """
        You have to set .selector before calling this method
        """
        if self.selector is None:
            return
        filter_ = self.selector.dynamic_pair_filter(self)
        if filter_ is None:
            return
        pair = type(self).objects.filter(filter_).first()
        if pair:
            pair.data_source = self.data_source
            pair.poller = self.poller
        return pair

    @property
    def primary_ip(self):
        if self.prefer_ipv4 is None:
            return super().primary_ip
        if self.prefer_ipv4 and self.primary_ip4:
            return self.primary_ip4
        elif self.primary_ip6:
            return self.primary_ip6
        elif self.primary_ip4:
            return self.primary_ip4
        else:
            return None
