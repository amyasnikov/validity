import datetime
import operator
from dataclasses import dataclass, field
from functools import reduce
from itertools import chain
from typing import Annotated, Any, Callable

from core.choices import JobStatusChoices
from core.models import Job
from dimi import Singleton
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from extras.choices import ObjectChangeActionChoices

from validity import di
from validity.models import ComplianceReport
from validity.netbox_changes import enqueue_object, events_queue
from ..data_models import FullRunTestsParams, Message, TestResultRatio
from ..launch import Launcher
from ..logger import Logger
from ..parent_jobs import JobExtractor
from .base import TerminateMixin


def enqueue(report, request, action):
    return enqueue_object(events_queue.get(), report, request.get_user(), request.id, action)


@di.dependency(scope=Singleton)
@dataclass(repr=False, kw_only=True)
class CombineWorker(TerminateMixin):
    log_factory: Callable[[], Logger] = Logger
    job_extractor_factory: Callable[[], JobExtractor] = JobExtractor
    enqueue_func: Callable[[ComplianceReport, HttpRequest, str], None] = enqueue
    report_queryset: QuerySet[ComplianceReport] = field(
        default_factory=ComplianceReport.objects.annotate_result_stats().count_devices_and_tests
    )

    def fire_report_webhook(self, report_id: int, request: HttpRequest) -> None:
        report = self.report_queryset.get(pk=report_id)
        self.enqueue_func(report, request, ObjectChangeActionChoices.ACTION_CREATE)

    def count_test_stats(self, job_extractor: JobExtractor) -> TestResultRatio:
        result_ratios = (parent.job.result.test_stat for parent in job_extractor.parents)
        return reduce(operator.add, result_ratios)

    def collect_logs(self, logger: Logger, job_extractor: JobExtractor) -> list[Message]:
        parent_logs = chain.from_iterable(extractor.job.result.log for extractor in job_extractor.parents)
        grandparent_logs = job_extractor.parent.parent.job.result.log
        return [*grandparent_logs, *parent_logs, *logger.messages]

    def terminate_succeeded_job(self, job: Job, test_stats: TestResultRatio, logs: list[Message]):
        job.data = {"log": [log.serialized for log in logs], "output": {"statistics": test_stats.serialized}}
        job.terminate()

    @di.inject
    def schedule_next_job(
        self, params: FullRunTestsParams, job: Job, launcher: Annotated[Launcher, "runtests_launcher"]
    ) -> None:
        if params.schedule_interval:
            params.schedule_at = job.started + datetime.timedelta(params.schedule_interval)
            launcher(params)

    def get_previous_errors(self, job_extractor: JobExtractor) -> list[Message]:
        error_logs = chain.from_iterable(
            extractor.job.result.log for extractor in job_extractor.parents if extractor.job.result.errored
        )
        return list(error_logs)

    def __call__(self, params: FullRunTestsParams) -> Any:
        netbox_job = params.get_job()
        with self.terminate_job_on_error(netbox_job):
            job_extractor = self.job_extractor_factory()
            if err_logs := self.get_previous_errors(job_extractor):
                self.terminate_job(netbox_job, JobStatusChoices.STATUS_ERRORED, error="ApplyWorkerError", logs=err_logs)
                return
            logger = self.log_factory()
            self.fire_report_webhook(params.report_id, params.request)
            test_stats = self.count_test_stats(job_extractor)
            report_url = reverse("plugins:validity:compliancereport", kwargs={"pk": params.report_id})
            logger.success(f"Job succeeded. See [Compliance Report]({report_url}) for detailed statistics")
            logs = self.collect_logs(logger, job_extractor)
            self.schedule_next_job(params, netbox_job)
            self.terminate_job(
                netbox_job, JobStatusChoices.STATUS_COMPLETED, logs=logs, output={"statistics": test_stats.serialized}
            )
