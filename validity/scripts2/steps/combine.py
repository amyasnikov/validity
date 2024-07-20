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
from validity.utils.orm import TwoPhaseTransaction
from ..data_models import FullScriptParams, Message, TestResultRatio
from ..logger import Logger
from ..parent_jobs import JobExtractor
from .apply import execute_tests
from .base import TracebackMixin


@dataclass
class CombineWorker(TracebackMixin):
    log_factory: Callable[[], Logger]
    job_extractor_factory: Callable[[], JobExtractor]
    enqueue_func: Callable[[ComplianceReport, HttpRequest, str], None]
    report_queryset: QuerySet[ComplianceReport]
    commit_func: Callable[[str], None]
    transaction_template: str

    def commit_transactions(self, workers_num: int, job_id: int) -> None:
        for worker_id in range(workers_num):
            transaction_id = self.transaction_template.format(job=job_id, worker=worker_id)
            self.commit_func(transaction_id)

    def fire_report_webhook(self, report_id: int, request: HttpRequest) -> None:
        report = self.report_queryset.get(pk=report_id)
        self.enqueue_func(report, request, ObjectChangeActionChoices.ACTION_CREATE)

    def count_test_stats(self, job_extractor: JobExtractor) -> TestResultRatio:
        result_ratios = (parent.job.result.test_stat for parent in job_extractor.parents)
        return reduce(operator.add, result_ratios)

    def collect_logs(self, logger: Logger, job_extractor: JobExtractor) -> list[Message]:
        assert job_extractor.parents, "Combine must have parents"
        parent_logs = chain.from_iterable(extractor.job.result.log for extractor in job_extractor.parents)
        grandparent_logs = job_extractor.parent.parent.job.result.log
        return [*grandparent_logs, *parent_logs, *logger.messages]

    def terminate_job(self, job: Job, test_stats: TestResultRatio, logs: list[Message]):
        job.data = {"log": [log.serialized for log in logs], "output": {"statistics": test_stats.serialized}}
        job.terminate()

    def schedule_next_job(self, interval: int) -> None:
        pass

    def __call__(self, params: FullScriptParams) -> Any:
        netbox_job = params.get_job()
        with self.terminate_job_on_error(netbox_job):
            logger = self.log_factory()
            job_extractor = self.job_extractor_factory()
            self.commit_transactions(params.workers_num, params.job_id)
            self.fire_report_webhook(params.report_id, params.request)
            test_stats = self.count_test_stats(job_extractor)
            report_url = reverse("plugins:validity:compliancereport", kwargs={"pk": params.report_id})
            logger.success(f"Job succeeded. See [Compliance Report]({report_url}) for detailed statistics")
            logs = self.collect_logs(logger, job_extractor)
            self.terminate_job(netbox_job, test_stats, logs)
            if params.schedule_interval:
                self.schedule_next_job(params.schedule_interval)


def enqueue(report, request, action):
    return enqueue_object(events_queue.get(), report, request.user, request.id, action)


def two_phase_commit(transaction_id):
    TwoPhaseTransaction(transaction_id).commit()


combine_work = CombineWorker(
    log_factory=Logger,
    job_extractor_factory=JobExtractor,
    enqueue_func=enqueue,
    transaction_template=execute_tests.transaction_template,
    commit_func=two_phase_commit,
    report_queryset=ComplianceReport.objects.annotate_result_stats().count_devices_and_tests(),
)
