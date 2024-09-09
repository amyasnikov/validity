from dataclasses import dataclass, field
from itertools import chain, cycle, groupby, repeat
from typing import Callable, Iterable

from dimi import Singleton
from django.db.models import Q, QuerySet

from validity import di
from validity.models import ComplianceSelector, VDataSource, VDevice
from validity.utils.misc import batched, datasource_sync
from ..data_models import FullRunTestsParams, SplitResult
from ..exceptions import AbortScript
from ..logger import Logger
from .base import TerminateMixin


@di.dependency(scope=Singleton)
@dataclass(repr=False)
class SplitWorker(TerminateMixin):
    log_factory: Callable[[], Logger] = Logger
    datasource_sync_fn: Callable[[Iterable[VDataSource], Q], None] = datasource_sync
    device_batch_size: int = 2000
    datasource_queryset: QuerySet[VDataSource] = field(default_factory=VDataSource.objects.all)
    device_queryset: QuerySet[VDevice] = field(default_factory=VDevice.objects.all)

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

    def sync_datasources(self, overriding_datasource: int | None, device_filter: Q, logger: Logger):
        datasources = self.datasources_to_sync(overriding_datasource, device_filter)
        if datasources.exists():
            self.datasource_sync_fn(datasources, device_filter)
            logger.info(
                "The following Data Sources have been synced: "
                + ", ".join(sorted(f'"{ds.name}"' for ds in datasources))
            )
        else:
            logger.warning("No bound Data Sources found. Sync skipped")

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
        with self.terminate_job_on_error(job):
            job.start()
            job.object_type.model_class().objects.delete_old()
            logger = self.log_factory()
            device_filter = params.get_device_filter()
            if params.sync_datasources:
                self.sync_datasources(params.overriding_datasource, device_filter, logger)
            slices = self.distribute_work(params, logger, device_filter)
            return SplitResult(log=logger.messages, slices=slices)
