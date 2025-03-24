import logging

from dimi import Container
from netbox.plugins import PluginConfig
from netbox.settings import VERSION

from validity.utils.version import NetboxVersion


logger = logging.getLogger(__name__)


class NetBoxValidityConfig(PluginConfig):
    name = "validity"
    verbose_name = "Validity"
    description = "Write and run auto tests for network devices"
    author = "Anton Miasnikov"
    author_email = "anton2008m@gmail.com"
    version = "3.1.3"
    base_url = "validity"
    django_apps = ["django_bootstrap5"]
    min_version = "4.0.0"

    # custom field
    netbox_version = NetboxVersion(VERSION)

    def _setup_queues(self):
        django_settings = di["django_settings"]
        for _, queue_name in di["validity_settings"].custom_queues:
            if queue_name not in django_settings.RQ_QUEUES:
                django_settings.RQ_QUEUES[queue_name] = django_settings.RQ_PARAMS

    def ready(self):
        from validity import dependencies, signals

        self._setup_queues()
        return super().ready()


config = NetBoxValidityConfig


di = Container()
