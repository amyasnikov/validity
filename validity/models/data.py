import logging
from contextlib import contextmanager
from itertools import chain

from core.choices import DataSourceStatusChoices
from core.exceptions import SyncError
from core.models import DataFile, DataSource
from core.signals import post_sync, pre_sync
from django.db.models import Q
from django.utils import timezone

from validity.j2_env import Environment
from validity.managers import VDataFileQS, VDataSourceQS
from validity.utils.misc import batched


logger = logging.getLogger(__name__)


class VDataFile(DataFile):
    objects = VDataFileQS.as_manager()

    class Meta:
        proxy = True


class VDataSource(DataSource):
    objects = VDataSourceQS.as_manager()

    class Meta:
        proxy = True

    @property
    def is_default(self):
        return self.cf.get("default", False)

    @property
    def web_url(self) -> str:
        template_text = self.cf.get("web_url") or ""
        template = Environment().from_string(template_text)
        return template.render(**self.parameters or {})

    @property
    def config_path_template(self) -> str:
        return self.cf.get("device_config_path") or ""

    @property
    def command_path_template(self) -> str:
        return self.cf.get("device_command_path") or ""

    def get_config_path(self, device) -> str:
        return Environment().from_string(self.config_path_template).render(device=device)

    def get_command_path(self, device, command) -> str:
        return Environment().from_string(self.command_path_template).render(device=device, command=command)

    @contextmanager
    def _sync_status(self):
        if self.status == DataSourceStatusChoices.SYNCING:
            raise SyncError("Cannot initiate sync; syncing already in progress.")
        pre_sync.send(sender=self.__class__, instance=self)
        self.status = DataSourceStatusChoices.SYNCING
        DataSource.objects.filter(pk=self.pk).update(status=self.status)
        try:
            yield
            self.status = DataSourceStatusChoices.COMPLETED
        except Exception:
            self.status = DataSourceStatusChoices.FAILED
            raise
        finally:
            self.last_synced = timezone.now()
            DataSource.objects.filter(pk=self.pk).update(status=self.status, last_synced=self.last_synced)
            post_sync.send(sender=self.__class__, instance=self)

    def partial_sync(self, device_filter: Q, batch_size: int = 1000) -> None:
        def update_batch(batch):
            for datafile in self.datafiles.filter(path__in=batch).iterator():
                if datafile.refresh_from_disk(local_path):
                    yield datafile
                paths.discard(datafile.path)

        def new_data_file(path):
            df = DataFile(source=self, path=path)
            df.refresh_from_disk(local_path)
            df.full_clean()
            return df

        if self.type != "device_polling":
            raise SyncError("Partial sync is available only for Data Source with type Device Polling")
        backend = self.get_backend()
        with backend.fetch(device_filter) as local_path, self._sync_status():
            paths = self._walk(local_path)
            datafiles_to_update = chain.from_iterable(
                update_batch(path_batch) for path_batch in batched(paths, batch_size)
            )
            updated = DataFile.objects.bulk_update(
                datafiles_to_update, batch_size=batch_size, fields=("last_updated", "size", "hash", "data")
            )
            new_datafiles = (new_data_file(path) for path in paths)
            created = len(DataFile.objects.bulk_create(new_datafiles, batch_size=batch_size))
            logger.debug("%s new files were created and %s existing files were updated during sync", created, updated)

    def sync(self, device_filter: Q | None = None):
        if device_filter is not None and self.type == "device_polling":
            return self.partial_sync(device_filter)
        return super().sync()
