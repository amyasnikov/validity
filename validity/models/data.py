from functools import cached_property

from core.models import DataFile, DataSource
from jinja2 import BaseLoader, Environment

from validity.managers import VDataFileQS, VDataSourceQS
from validity.utils.orm import QuerySetMap


class VDataFile(DataFile):
    objects = VDataFileQS.as_manager()

    class Meta:
        proxy = True


class VDataSource(DataSource):
    objects = VDataSourceQS.as_manager()

    @cached_property
    def configfiles_by_path(self) -> QuerySetMap:
        """
        Returns "path: datafile" mapping for config files
        """
        assert hasattr(self, "config_files"), "You must call .prefetch_config_files() first"
        return QuerySetMap(self.config_files.all(), attribute="path")

    class Meta:
        proxy = True

    @property
    def is_default(self):
        return self.cf.get("device_config_default", False)

    @property
    def web_url(self) -> str:
        template_text = self.cf.get("web_url", "")
        template = Environment(loader=BaseLoader()).from_string(template_text)
        return template.render(**self.parameters or {})

    @property
    def config_path_template(self) -> str:
        return self.cf.get("device_config_path", "")
