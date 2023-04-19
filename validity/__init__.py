import logging
import os
from pathlib import Path

from django.conf import settings as django_settings
from extras.plugins import PluginConfig
from pydantic import BaseModel, DirectoryPath, Field


logger = logging.getLogger(__name__)


class NetBoxValidityConfig(PluginConfig):
    name = "validity"
    verbose_name = "Validity: Configuration Compliance"
    description = "Vendor-agnostic framework to build your own configuration compliance rule set"
    author = "Anton Miasnikov"
    author_email = "anton2008m@gmail.com"
    version = "1.0.0"
    base_url = "validity"
    django_apps = ["bootstrap5"]

    def ready(self):
        try:
            os.makedirs(settings.git_folder, exist_ok=True)
        except OSError as e:
            if not settings.git_folder.is_dir():
                logger.error("Cannot create git_folder (%s), %s: %s", settings.git_folder, type(e).__name__, e)
        return super().ready()


config = NetBoxValidityConfig


class ValiditySettings(BaseModel):
    store_last_results: int = Field(default=5, gt=0, lt=1001)
    store_reports: int = Field(default=5, gt=0, lt=1001)
    git_folder: DirectoryPath = Path("/opt/git_repos")
    sleep_between_tests: float = 0


settings = ValiditySettings.parse_obj(django_settings.PLUGINS_CONFIG.get("validity", {}))
