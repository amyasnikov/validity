from contextlib import contextmanager

from core.choices import JobStatusChoices
from core.models import Job


class TerminateMixin:
    def terminate_job(self, job: Job, status: str, error: str | None = None, logs=None, output=None):
        logs = logs or []
        job.data = {"log": [log.serialized for log in logs], "output": output}
        job.terminate(status, error)

    def terminate_errored_job(self, job: Job, type, value, traceback):
        logger = self.log_factory()
        logger.log_exception(value, type, traceback)
        logger.info("Database changes have been reverted")
        self.terminate_job(job, status=JobStatusChoices.STATUS_ERRORED, error=repr(value), logs=logger.messages)

    @contextmanager
    def terminate_job_on_error(self, job: Job):
        try:
            yield
        except Exception as err:
            self.terminate_errored_job(job, type(err), err, err.__traceback__)
            raise
