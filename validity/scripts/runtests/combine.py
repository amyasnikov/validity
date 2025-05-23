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
from django.urls import reverse
from extras.events import enqueue_event, flush_events

from validity import di
from validity.models import ComplianceReport, ComplianceTestResult
from validity.utils.logger import Logger, Message
from ..data_models import FullRunTestsParams, RequestInfo, TestResultRatio
from ..exceptions import AbortScript
from ..keeper import JobKeeper
from ..launch import Launcher
from ..parent_jobs import JobExtractor


def enqueue(report: ComplianceReport, request: RequestInfo):
    queue = {}
    enqueue_event(queue, report, request.get_user(), request.id, "object_created")
    flush_events(queue.values())


@di.dependency(scope=Singleton)
@dataclass(repr=False, kw_only=True)
class CombineWorker:
    jobkeeper_factory: Callable[[Job], JobKeeper] = JobKeeper
    job_extractor_factory: Callable[[], JobExtractor] = JobExtractor
    enqueue_func: Callable[[ComplianceReport, RequestInfo], None] = enqueue
    report_queryset: QuerySet[ComplianceReport] = field(
        default_factory=ComplianceReport.objects.annotate_result_stats().count_devices_and_tests
    )
    testresult_queryset: QuerySet[ComplianceTestResult] = field(default_factory=ComplianceTestResult.objects.all)

    def fire_report_webhook(self, report_id: int, request: RequestInfo) -> None:
        report = self.report_queryset.get(pk=report_id)
        self.enqueue_func(report, request)

    def count_test_stats(self, job_extractor: JobExtractor) -> TestResultRatio:
        result_ratios = (parent.job.result.test_stat for parent in job_extractor.parents)
        return reduce(operator.add, result_ratios)

    def collect_logs(self, logger: Logger, job_extractor: JobExtractor) -> list[Message]:
        parent_logs = chain.from_iterable(extractor.job.result.log for extractor in job_extractor.parents)
        grandparent_logs = job_extractor.parent.parent.job.result.log
        return [*grandparent_logs, *parent_logs, *logger.messages]

    def compose_logs(self, logger, job_extractor, report_id):
        report_url = reverse("plugins:validity:compliancereport", kwargs={"pk": report_id})
        logger.success(f"Job succeeded. See [Compliance Report]({report_url}) for detailed statistics")
        return self.collect_logs(logger, job_extractor)

    def terminate_succeeded_job(self, job: Job, test_stats: TestResultRatio, logs: list[Message]):
        job.data = {"log": [log.serialized for log in logs], "output": {"statistics": test_stats.serialized}}
        job.terminate()

    @di.inject
    def schedule_next_job(
        self, params: FullRunTestsParams, job: Job, launcher: Annotated[Launcher, "runtests_launcher"]
    ) -> None:
        if params.schedule_interval:
            params.schedule_at = job.started + datetime.timedelta(minutes=params.schedule_interval)
            launcher(params)

    def abort_if_apply_errors(self, job_extractor: JobExtractor) -> None:
        error_logs = list(
            chain.from_iterable(
                extractor.job.result.log for extractor in job_extractor.parents if extractor.job.result.errored
            )
        )
        if error_logs:
            raise AbortScript("ApplyWorkerError", status=JobStatusChoices.STATUS_ERRORED, logs=error_logs)

    def get_job_keeper(self, job: Job) -> JobKeeper:
        def error_callback(keeper, error):
            keeper.logger.info("Database changes have been reverted")
            self.testresult_queryset.filter(report_id=keeper.job.object_id).raw_delete()

        keeper = self.jobkeeper_factory(job)
        keeper.error_callback = error_callback
        return keeper

    def __call__(self, params: FullRunTestsParams) -> Any:
        netbox_job = params.get_job()
        with self.get_job_keeper(netbox_job) as keeper:
            job_extractor = self.job_extractor_factory()
            self.abort_if_apply_errors(job_extractor)
            self.fire_report_webhook(params.object_id, params.request)
            self.schedule_next_job(params, netbox_job)
            keeper.logger.messages = self.compose_logs(keeper.logger, job_extractor, params.object_id)
            test_stats = self.count_test_stats(job_extractor)
            keeper.terminate_job(JobStatusChoices.STATUS_COMPLETED, output={"statistics": test_stats.serialized})
