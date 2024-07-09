from dataclasses import dataclass
from itertools import chain, cycle, groupby, repeat
from typing import Callable, Iterable

from django.db.models import Q

from validity.models import VDataSource, VDevice
from validity.utils.misc import batched, datasource_sync
from .data_models import ScriptParams, SplitResult
from .logger import Logger


@dataclass
class SplitWorker:
    log: Logger
    datasource_sync_fn: Callable[[Iterable[VDataSource], Q]]
    device_batch_size: int

    def datasources_to_sync(self, script_params: ScriptParams) -> Iterable[VDataSource]:
        if script_params.override_datasource:
            return [VDataSource.objects.get(pk=script_params.override_datasource)]
        datasource_ids = (
            VDevice.objects.filter(script_params.device_filter)
            .annotate_datasource_id()
            .values_list("data_source_id", flat=True)
            .distinct()
        )
        return VDataSource.objects.filter(pk__in=datasource_ids)

    def sync_datasources(self, script_params: ScriptParams):
        if script_params.sync_datasources:
            datasources = self.datasources_to_sync(script_params)
            self.datasource_sync_fn(datasources, script_params.device_filter)

    def _work_slices(self, script_params: ScriptParams, devices_per_worker: int):
        def device_ids(selector):
            return (
                selector.devices.iterator(chunk_size=self.device_batch_size).order_by("pk").values_list("pk", flat=True)
            )

        selector_device = chain.from_iterable(
            zip(repeat(selector.pk), device_ids(selector)) for selector in script_params.selector_qs
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

    def distribute_work(self, script_params: ScriptParams) -> list[dict[int, list[int]]]:
        device_count = VDevice.objects.filter(script_params.device_filter).count()
        devices_per_worker = device_count // script_params.workers_num
        self.log.info(f"Running the tests for *{device_count} devices*")
        if (workers := script_params.workers_num) > 1:
            self.log.info(
                f"Distributing the work among {workers} workers. {devices_per_worker} devices handles each worker in average"
            )

        slices = [*self._work_slices(script_params, devices_per_worker)]

        # distribute the leftover among other slices
        if len(slices) > script_params.workers_num:
            self._eliminate_leftover(slices)
        return slices

    def __call__(self, **kwargs) -> SplitResult:
        script_params = ScriptParams.model_validate(kwargs)
        self.sync_datasources(script_params)
        slices = self.distribute_work(script_params)
        return SplitResult(log=self.log.messages, slices=slices)


split_work = SplitWorker(log=Logger(), datasource_sync_fn=datasource_sync, device_batch_size=2000)
