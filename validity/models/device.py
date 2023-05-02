from functools import cached_property
from typing import Any, Optional

from dcim.models import Device

from validity.config_compliance.device_config import DeviceConfig
from validity.managers import VDeviceQS
from .repo import GitRepo
from .serializer import ConfigSerializer


def encrypted_password_to_field(json_repo: dict) -> None:
    json_repo["encrypted_password"] = GitRepo._meta.get_field("encrypted_password").to_python(
        json_repo["encrypted_password"]
    )


class VDevice(Device):
    objects = VDeviceQS.as_manager()

    class Meta:
        proxy = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.selector = None

    def annotated_repo(self) -> GitRepo | None:
        if not getattr(self, "json_repo", None):
            return
        encrypted_password_to_field(self.json_repo)
        return GitRepo(**self.json_repo)

    @cached_property
    def repo(self) -> GitRepo | None:
        if annotated := self.annotated_repo():
            return annotated
        default = GitRepo.objects.filter(default=True).first()
        if default:
            return default
        try:
            return self.tenant.cf.get("repo")
        except AttributeError:
            return

    def annotated_serializer(self) -> ConfigSerializer | None:
        if not getattr(self, "json_serializer", None):
            return
        if getattr(self, "json_serializer_repo", None):
            encrypted_password_to_field(self.json_serializer_repo)
            self.json_serializer["repo"] = GitRepo(**self.json_serializer_repo)
        return ConfigSerializer(**self.json_serializer)

    @cached_property
    def serializer(self) -> ConfigSerializer | None:
        if annotated := self.annotated_serializer():
            return annotated
        getters = [
            lambda obj: obj.cf.get("serializer"),
            lambda obj: obj.device_type.cf.get("serializer"),
            lambda obj: obj.device_type.manufacturer.cf.get("serializer"),
        ]
        for getter in getters:
            result = getter(self)
            if result:
                return result

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
        return type(self).objects.filter(filter_).exclude(pk=self.pk).first()
