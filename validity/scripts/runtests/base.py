from contextlib import contextmanager
from dataclasses import dataclass, field

from core.choices import JobStatusChoices
from core.models import Job
from django.db.models import QuerySet

from validity.models import ComplianceTestResult
from ..exceptions import AbortScript


@dataclass(repr=False, kw_only=True)
class TerminateMixin:
    testresult_queryset: QuerySet[ComplianceTestResult] = field(default_factory=ComplianceTestResult.objects.all)

    def terminate_job(self, job: Job, status: str, error: str | None = None, logs=None, output=None):
        logs = logs or []
        job.data = {"log": [log.serialized for log in logs], "output": output}
        job.terminate(status, error)

    def terminate_errored_job(self, job: Job, error: Exception):
        logger = self.log_factory()
        if isinstance(error, AbortScript):
            logger.messages.extend(error.logs)
            logger.failure(str(error))
            status = error.status
        else:
            logger.log_exception(error)
            status = JobStatusChoices.STATUS_ERRORED
        logger.info("Database changes have been reverted")
        self.revert_db_changes(job)
        self.terminate_job(job, status=status, error=repr(error), logs=logger.messages)

    def revert_db_changes(self, job: Job) -> None:
        self.testresult_queryset.filter(report_id=job.object_id).raw_delete()

    @contextmanager
    def terminate_job_on_error(self, job: Job):
        try:
            yield
        except Exception as err:
            self.terminate_errored_job(job, err)
            raise
