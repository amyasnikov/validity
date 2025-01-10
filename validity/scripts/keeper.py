from dataclasses import dataclass, field
from typing import Callable

from core.choices import JobStatusChoices
from core.models import Job

from validity import di
from validity.utils.logger import Logger
from .exceptions import AbortScript


@dataclass
class JobKeeper:
    """
    Keeps proper state of the DB Job object during script execution
    """

    job: Job
    error_callbacks: list[Callable[[Job], None]] = field(default_factory=list)
    logger: Logger = field(default_factory=lambda: di["Logger"])

    def __enter__(self):
        self.job.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.terminate_errored_job(exc)
        elif self.job.status == JobStatusChoices.STATUS_RUNNING:
            self.terminate_job()
        self.logger.flush()

    def _exec_callbacks(self):
        for callback in self.error_callbacks:
            callback(self)

    def terminate_errored_job(self, error: Exception) -> None:
        self._exec_callbacks()
        if isinstance(error, AbortScript):
            self.logger.messages.extend(error.logs)
            self.logger.failure(str(error))
            status = error.status
        else:
            self.logger.log_exception(error)
            status = JobStatusChoices.STATUS_ERRORED
        self.terminate_job(status=status, error=repr(error))

    def terminate_job(
        self, status: str = JobStatusChoices.STATUS_COMPLETED, error: str | None = None, output=None
    ) -> None:
        self.job.data = self.job.data or {}
        self.job.data["log"] = [log.serialized for log in self.logger.messages]
        output = output or self.job.data.get("output")
        self.job.data["output"] = output
        self.job.terminate(status, error)
