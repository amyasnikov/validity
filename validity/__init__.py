from extras.plugins import PluginConfig
from pydantic import BaseModel, Field, DirectoryPath
from django.conf import settings as django_settings


class NetBoxValidityConfig(PluginConfig):
    name = 'validity'
    verbose_name = 'Validity: Configuration Compliance for Network Devices'
    description = 'This plugin provides simple framework to build your own configuration compliance rule set'
    version = '0.1'
    base_url = 'validity'
    django_apps = ["bootstrap5"]


config = NetBoxValidityConfig


class ValiditySettings(BaseModel):
    store_last_results: int = Field(default=5, gt=1, lt=1000)
    git_folder: DirectoryPath = Field(default='/etc/netbox/scripts')


settings = ValiditySettings.parse_obj(django_settings.PLUGINS_CONFIG.get("validity", {}))
