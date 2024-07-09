import operator
from dataclasses import dataclass
from functools import reduce
from itertools import chain
from typing import Any, Callable

from core.models import Job
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from extras.choices import ObjectChangeActionChoices

from validity.models import ComplianceReport
from validity.netbox_changes import enqueue_object, events_queue
from .data_models import CombineResult, Message, ScriptOutput, TestResultRatio
from .logger import Logger
from .parent_jobs import JobExtractor


@dataclass
class CombineWorker:
    log: Logger
    job_extractor: JobExtractor
    enqueue_func: Callable[[ComplianceReport, HttpRequest, str], None]
    job_queryset: QuerySet[Job]

    def fire_report_webhook(self, report_id: int, request: HttpRequest) -> None:
        report = ComplianceReport.objects.filter(pk=report_id).annotate_result_stats().count_devices_and_tests().first()
        self.enqueue_func(report, request, ObjectChangeActionChoices.ACTION_CREATE)

    def count_test_stats(self) -> TestResultRatio:
        result_ratios = (parent.job.result.test_stat for parent in self.job_extractor.parents)
        return reduce(operator.add, result_ratios)

    def collect_logs(self) -> list[Message]:
        assert self.job_extractor.parents, "Combine must have parents"
        parent_logs = chain.from_iterable(extractor.job.result.log for extractor in self.job_extractor.parents)
        grandparent_logs = self.job_extractor.parent.parent.job.result.log
        return [*grandparent_logs, *parent_logs, *self.log.messages]

    def __call__(self, job_id: int, request: HttpRequest) -> Any:
        job = self.job_queryset.get(pk=job_id)
        self.fire_report_webhook(job.object_id, request)
        test_stats = self.count_test_stats()
        report_url = reverse("plugins:validity:compliancereport", kwargs={"pk": job.object_id})
        self.log.info(f"See [Compliance Report]({report_url}) for detailed statistics")
        logs = self.collect_logs()
        return CombineResult(output=ScriptOutput(test_stats), log=logs)


def enqueue(report, request, action):
    return enqueue_object(events_queue.get(), report, request.user, request.id, action)


combine_work = CombineWorker(logger=Logger(), job_extractor=JobExtractor(), enqueue_func=enqueue)
