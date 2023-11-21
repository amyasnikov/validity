from functools import cached_property
from typing import Any, Optional

from dcim.models import Device
from jinja2 import BaseLoader, Environment

from validity.config_compliance.device_config import DeviceConfig
from validity.managers import VDeviceQS
from .data import VDataFile, VDataSource


class VDevice(Device):
    objects = VDeviceQS.as_manager()
    data_source: VDataSource
    # above this limit config data files won't be prefetched to datasource and will be queried one by one
    config_prefetch_limit = 1000

    class Meta:
        proxy = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.selector = None

    @property
    def config_path(self) -> str:
        assert hasattr(self, "data_source"), "You must prefetch datasource first"
        template = Environment(loader=BaseLoader()).from_string(self.data_source.config_path_template)
        return template.render(device=self)

    @cached_property
    def data_file(self) -> VDataFile | None:
        path = self.config_path
        if (
            hasattr(self.data_source, "config_files")
            and self.data_source.config_file_count <= self.config_prefetch_limit
        ):
            return self.data_source.configfiles_by_path.get(path)
        return self.data_source.datafiles.filter(path=path).first()

    @cached_property
    def device_config(self) -> DeviceConfig:
        return DeviceConfig.from_device(self)

    @cached_property
    def config(self) -> dict | list | None:
        return self.device_config.serialized

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
        return type(self).objects.filter(filter_).first()
