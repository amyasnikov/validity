import logging

from dimi import Container
from netbox.settings import VERSION

from validity.utils.version import NetboxVersion


if VERSION.startswith("3."):
    from extras.plugins import PluginConfig
else:
    from netbox.plugins import PluginConfig


logger = logging.getLogger(__name__)


class NetBoxValidityConfig(PluginConfig):
    name = "validity"
    verbose_name = "Validity"
    description = "Write and run auto tests for network devices"
    author = "Anton Miasnikov"
    author_email = "anton2008m@gmail.com"
    version = "3.0.4"
    base_url = "validity"
    django_apps = ["django_bootstrap5"]
    min_version = "3.7.0"

    # custom field
    netbox_version = NetboxVersion(VERSION)

    def _setup_queue(self):
        queue_name = di["validity_settings"].runtests_queue
        django_settings = di["django_settings"]
        if queue_name not in django_settings.RQ_QUEUES:
            django_settings.RQ_QUEUES[queue_name] = django_settings.RQ_PARAMS

    def ready(self):
        from validity import dependencies, signals

        self._setup_queue()
        return super().ready()


config = NetBoxValidityConfig


di = Container()
