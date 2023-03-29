from pathlib import Path

from django.conf import settings as django_settings
from extras.plugins import PluginConfig
from pydantic import BaseModel, DirectoryPath, Field


class NetBoxValidityConfig(PluginConfig):
    name = "validity"
    verbose_name = "Validity: Configuration Compliance"
    description = "Vendor agnostic framework to build your own configuration compliance rule set"
    version = "0.1.0"
    base_url = "validity"
    django_apps = ["bootstrap5"]


config = NetBoxValidityConfig


class ValiditySettings(BaseModel):
    store_last_results: int = Field(default=5, gt=0, lt=1001)
    store_reports: int = Field(default=5, gt=0, lt=1001)
    git_folder: DirectoryPath = Path("/opt/git_repos")
    sleep_between_tests: float = 0


settings = ValiditySettings.parse_obj(django_settings.PLUGINS_CONFIG.get("validity", {}))
