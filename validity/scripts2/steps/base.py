import traceback as tb
from contextlib import contextmanager

from core.choices import JobStatusChoices
from core.models import Job


class TracebackMixin:
    def get_traceback_logs(self, type, value, traceback):
        logger = self.log_factory()
        stacktrace = tb.format_tb(traceback)
        logger.failure(f"Unhandled error occured: `{type}: {value}`\n```\n{stacktrace}\n```")
        logger.info("Database changes have been reverted")
        return logger.messages

    def terminate_job(self, job: Job, type, value, traceback):
        job.data = {"log": [log.serialized for log in self.get_traceback_logs(type, value, traceback)], "output": {}}
        job.terminate(JobStatusChoices.STATUS_ERRORED, error=repr(value))

    def remove_report(self, job):
        report = job.object
        job.object_id = None
        job.save()
        report.delete()

    @contextmanager
    def terminate_job_on_error(self, job: Job):
        try:
            yield
        except Exception as err:
            self.terminate_job(job, type(err), err, err.__traceback__)
            self.remove_report(job)
            raise
