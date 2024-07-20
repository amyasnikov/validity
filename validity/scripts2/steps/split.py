from dataclasses import dataclass
from itertools import chain, cycle, groupby, repeat
from typing import Callable, Iterable

from django.db.models import Q, QuerySet

from validity.models import ComplianceSelector, VDataSource, VDevice
from validity.utils.misc import batched, datasource_sync
from ..data_models import FullScriptParams, SplitResult
from ..logger import Logger
from .base import TracebackMixin


@dataclass
class SplitWorker(TracebackMixin):
    log_factory: Callable[[], Logger]
    datasource_sync_fn: Callable[[Iterable[VDataSource], Q]]
    device_batch_size: int
    datasource_queryset: QuerySet[VDataSource]
    device_queryset: QuerySet[VDevice]

    def datasources_to_sync(self, override_datasource: int | None, device_filter: Q) -> Iterable[VDataSource]:
        if override_datasource:
            return [self.datasource_queryset.get(pk=override_datasource)]
        datasource_ids = (
            self.datasource_queryset.filter(device_filter)
            .annotate_datasource_id()
            .values_list("data_source_id", flat=True)
            .distinct()
        )
        return self.datasource_queryset.filter(pk__in=datasource_ids)

    def sync_datasources(self, override_datasource: int | None, device_filter: Q):
        datasources = self.datasources_to_sync(override_datasource, device_filter)
        self.datasource_sync_fn(datasources, device_filter)

    def _work_slices(self, selector_qs: QuerySet[ComplianceSelector], devices_per_worker: int):
        def device_ids(selector):
            return (
                selector.devices.iterator(chunk_size=self.device_batch_size).order_by("pk").values_list("pk", flat=True)
            )

        selector_device = chain.from_iterable(
            zip(repeat(selector.pk), device_ids(selector)) for selector in selector_qs
        )
        for batch in batched(selector_device, devices_per_worker, tuple):
            yield {
                selector: [dev_id for _, dev_id in grouped_pairs]
                for selector, grouped_pairs in groupby(batch, key=lambda pair: pair[0])
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
        self, workers_num: int, device_filter: Q, selectors: QuerySet[ComplianceSelector], logger: Logger
    ) -> list[dict[int, list[int]]]:
        device_count = self.device_queryset.filter(device_filter).count()
        devices_per_worker = device_count // workers_num
        logger.info(f"Running the tests for *{device_count} devices*")
        if workers_num > 1:
            logger.info(
                f"Distributing the work among {workers_num} workers. {devices_per_worker} devices handles each worker in average"
            )

        slices = [*self._work_slices(selectors, devices_per_worker)]

        # distribute the leftover among other slices
        if len(slices) > workers_num:
            self._eliminate_leftover(slices)
        return slices

    def __call__(self, params: FullScriptParams) -> SplitResult:
        with self.terminate_job_on_error(params.get_job()):
            logger = self.log_factory()
            device_filter = params.get_device_filter()
            if params.sync_datasources:
                self.sync_datasources(params.override_datasource, device_filter)
            slices = self.distribute_work(params.workers_num, device_filter, params.selector_qs, logger)
            return SplitResult(log=logger.messages, slices=slices)


split_work = SplitWorker(
    log_factory=Logger,
    datasource_sync_fn=datasource_sync,
    device_batch_size=2000,
    datasource_queryset=VDataSource.objects.all(),
    device_queryset=VDevice.objects.all(),
)
