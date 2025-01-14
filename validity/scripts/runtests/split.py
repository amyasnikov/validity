from dataclasses import dataclass, field
from functools import partial
from itertools import chain, cycle, groupby, repeat
from typing import Any, Callable, Collection, Iterable, Protocol

from core.models import Job
from dimi import Singleton
from django.db.models import Q, QuerySet

from validity import di
from validity.models import BackupPoint, ComplianceSelector, VDataSource, VDevice
from validity.utils.bulk import bulk_backup, datasource_sync
from validity.utils.logger import Logger
from validity.utils.misc import batched, md_link
from ..data_models import FullRunTestsParams, SplitResult
from ..exceptions import AbortScript
from ..keeper import JobKeeper


class BackupFn(Protocol):
    def __call__(
        self, backup_points: Collection[BackupPoint], *, fail_handler: Callable[["BackupPoint", Exception], Any]
    ) -> None: ...


@di.dependency(scope=Singleton)
@dataclass(repr=False)
class SplitWorker:
    jobkeeper_factory: Callable[[Job], JobKeeper] = partial(JobKeeper, auto_terminate=False)
    datasource_sync_fn: Callable[[Iterable[VDataSource], Q], None] = datasource_sync
    backup_fn: BackupFn = bulk_backup
    device_batch_size: int = 2000
    datasource_queryset: QuerySet[VDataSource] = field(
        default_factory=VDataSource.objects.set_attribute("permit_backup", False).all
    )
    device_queryset: QuerySet[VDevice] = field(default_factory=VDevice.objects.all)
    backup_queryset: QuerySet[BackupPoint] = field(
        default_factory=BackupPoint.objects.filter(backup_after_sync=True).all
    )

    def datasources_to_sync(self, overriding_datasource: int | None, device_filter: Q) -> QuerySet[VDataSource]:
        if overriding_datasource:
            return self.datasource_queryset.filter(pk=overriding_datasource)
        datasource_ids = (
            self.device_queryset.filter(device_filter)
            .annotate_datasource_id()
            .values_list("data_source_id", flat=True)
            .distinct()
        )
        return self.datasource_queryset.filter(pk__in=datasource_ids)

    def sync_datasources(
        self, overriding_datasource: int | None, device_filter: Q, logger: Logger
    ) -> QuerySet[VDataSource]:
        datasources = self.datasources_to_sync(overriding_datasource, device_filter)
        if datasources.exists():
            self.datasource_sync_fn(datasources, device_filter)
            logger.info("The following Data Sources have been synced: " + ", ".join(md_link(ds) for ds in datasources))
        else:
            logger.warning("No bound Data Sources found. Sync skipped")
        return datasources

    def backup_datasources(self, datasources: QuerySet[VDataSource], logger: Logger) -> None:
        def fail_handler(backup_point, error):
            logger.failure(f"Cannot back up {md_link(backup_point)}. {error}")
            failed_bp.add(backup_point)

        failed_bp = set()
        backup_points = set(self.backup_queryset.filter(data_source__in=datasources))
        self.backup_fn(backup_points, fail_handler=fail_handler)
        bp_names = ", ".join(md_link(bp) for bp in backup_points - failed_bp)
        if bp_names:
            logger.info(f"Data Sources have been backed up using the following Backup Points: {bp_names}")

    def _work_slices(
        self, selector_qs: QuerySet[ComplianceSelector], specific_devices: list[int], devices_per_worker: int
    ):
        def get_device_ids(selector):
            qs = selector.devices.filter(pk__in=specific_devices) if specific_devices else selector.devices
            return qs.order_by("pk").values_list("pk", flat=True).iterator(chunk_size=self.device_batch_size)

        selector_device = chain.from_iterable(
            zip(repeat(selector.pk), get_device_ids(selector)) for selector in selector_qs
        )
        for batch in batched(selector_device, devices_per_worker, tuple):
            yield {
                selector: device_ids
                for selector, grouped_pairs in groupby(batch, key=lambda pair: pair[0])
                if (device_ids := [dev_id for _, dev_id in grouped_pairs])
            }

    def _eliminate_leftover(self, slices):
        leftover = slices.pop()
        for slice in cycle(slices):
            if not leftover:
                break
            selector, devices = leftover.popitem()
            slice.setdefault(selector, [])
            slice[selector].extend(devices)

    def distribute_work(
        self, params: FullRunTestsParams, logger: Logger, device_filter: Q
    ) -> list[dict[int, list[int]]]:
        """
        Split all the devices under test into N slices where N is the number of workers
        Returns list of {selector_id: [device_id_1, device_id_2, ...]}
        """
        device_count = self.device_queryset.filter(device_filter).count()
        if not (devices_per_worker := device_count // params.workers_num):
            raise AbortScript(
                f"The number of workers ({params.workers_num}) "
                f"cannot be larger than the number of devices ({device_count})"
            )
        logger.info(f"Running the tests for *{device_count} devices*")
        if params.workers_num > 1:
            logger.info(
                f"Distributing the work among {params.workers_num} workers. "
                f"Each worker handles {devices_per_worker} device(s) in average"
            )

        slices = [*self._work_slices(params.selector_qs, params.devices, devices_per_worker)]

        # distribute the leftover among other slices
        if len(slices) > params.workers_num:
            self._eliminate_leftover(slices)
        return slices

    def __call__(self, params: FullRunTestsParams) -> SplitResult:
        job = params.get_job()
        with self.jobkeeper_factory(job) as keeper:
            job.object_type.model_class().objects.delete_old()
            device_filter = params.get_device_filter()
            if params.sync_datasources:
                datasources = self.sync_datasources(params.overriding_datasource, device_filter, keeper.logger)
                self.backup_datasources(datasources, keeper.logger)
            slices = self.distribute_work(params, keeper.logger, device_filter)
            return SplitResult(log=keeper.logger.messages, slices=slices)
