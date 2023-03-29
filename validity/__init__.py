from pathlib import Path

from django.conf import settings as django_settings
from extras.plugins import PluginConfig
from pydantic import BaseModel, DirectoryPath, Field

from validity.copy_scripts import copy_scripts


class NetBoxValidityConfig(PluginConfig):
    name = "validity"
    verbose_name = "Validity: Configuration Compliance"
    description = "Simple framework to build your own configuration compliance rule set"
    version = "0.1.0"
    base_url = "validity"
    django_apps = ["bootstrap5"]

    plugin_scripts_dir = "scripts"

    def ready(self):
        if settings.autocopy_scripts:
            copy_scripts(Path(__file__).parent / self.plugin_scripts_dir, Path(django_settings.SCRIPTS_ROOT))
        return super().ready()


config = NetBoxValidityConfig


class ValiditySettings(BaseModel):
    store_last_results: int = Field(default=5, gt=0, lt=1001)
    store_reports: int = Field(default=5, gt=0, lt=1001)
    git_folder: DirectoryPath = Path("/opt/git_repos")
    autocopy_scripts: bool = False
    sleep_between_tests: float = 0


settings = ValiditySettings.parse_obj(django_settings.PLUGINS_CONFIG.get("validity", {}))
