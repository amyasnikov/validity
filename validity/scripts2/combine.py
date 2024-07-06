import operator
from dataclasses import dataclass
from functools import reduce
from typing import Any, Callable

from django.http import HttpRequest
from extras.choices import ObjectChangeActionChoices

from validity.models import ComplianceReport
from validity.netbox_changes import enqueue_object, events_queue
from .logger import Logger
from .parent_jobs import JobExtractor


@dataclass
class CombineWorker:
    logger: Logger
    job_extractor: JobExtractor
    enqueue_func: Callable[[ComplianceReport, HttpRequest, str], None]

    def fire_report_webhook(self, report_id: int, request: HttpRequest) -> None:
        report = ComplianceReport.objects.filter(pk=report_id).annotate_result_stats().count_devices_and_tests().first()
        self.enqueue_func(report, request, ObjectChangeActionChoices.ACTION_CREATE)

    def count_test_stats(self):
        result_ratios = (parent.job.result.test_stat for parent in self.job_extractor.parents)
        return reduce(operator.add, result_ratios)

    def __call__(self, job_id: int, request: HttpRequest) -> Any:
        pass


def enqueue(report, request, action):
    return enqueue_object(events_queue.get(), report, request.user, request.id, action)


combine_work = CombineWorker(logger=Logger(), job_extractor=JobExtractor(), enqueue_func=enqueue)
