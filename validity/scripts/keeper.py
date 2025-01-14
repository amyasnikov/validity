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
    error_callback: Callable[["JobKeeper", Exception], None] = lambda *_: None  # noqa: E731
    logger: Logger = field(default_factory=lambda: di["Logger"])
    auto_terminate: bool = True

    def __enter__(self):
        self.job.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        with self.logger:
            if exc_type:
                return self.terminate_errored_job(exc)
            elif self.job.status == JobStatusChoices.STATUS_RUNNING and self.auto_terminate:
                self.terminate_job()

    def terminate_errored_job(self, error: Exception) -> bool:
        if isinstance(error, AbortScript):
            self.logger.messages.extend(error.logs)
            self.logger.failure(str(error))
            status = error.status
        else:
            self.logger.log_exception(error)
            status = JobStatusChoices.STATUS_ERRORED
        self.error_callback(self, error)
        self.terminate_job(status=status, error=repr(error))
        return isinstance(error, AbortScript)

    def terminate_job(
        self, status: str = JobStatusChoices.STATUS_COMPLETED, error: str | None = None, output=None
    ) -> None:
        self.job.data = self.job.data or {}
        self.job.data["log"] = [log.serialized for log in self.logger.messages]
        output = output or self.job.data.get("output")
        self.job.data["output"] = output
        self.job.terminate(status, error)
