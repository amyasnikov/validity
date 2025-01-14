import datetime
import logging
import traceback as tb
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partialmethod
from typing import Literal

from django.utils import timezone
from extras.choices import LogLevelChoices


logger = logging.getLogger("validity")


@dataclass(slots=True, frozen=True)
class Message:
    """
    Log message suitable for scripts
    """

    status: Literal["debug", "info", "failure", "warning", "success", "default"]
    message: str
    time: datetime.datetime = field(default_factory=lambda: timezone.now())
    script_id: str | None = None

    @property
    def serialized(self) -> dict:
        msg = self.message
        if self.script_id:
            msg = f"{self.script_id}, {msg}"
        return {"status": self.status, "message": msg, "time": self.time.isoformat()}


class Logger:
    """
    Collects the logs in the format of NetBox Custom Script
    """

    SYSTEM_LEVELS = {
        "debug": logging.DEBUG,
        "default": logging.INFO,
        "success": logging.INFO,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "failure": logging.ERROR,
    }

    def __init__(self) -> None:
        self.messages = []
        self._script_id = None

    def __enter__(self) -> "Logger":
        return self

    def __exit__(self, ty, exc, val):
        self.flush()

    @contextmanager
    def script_id(self, script_id: str):
        try:
            self._script_id = script_id
            yield self
        finally:
            self.flush()

    def _log(self, message: str, level: Literal["debug", "info", "failure", "warning", "success", "default"]):
        msg = Message(level, message, script_id=self._script_id)
        self.messages.append(msg)
        logger.log(self.SYSTEM_LEVELS[level], message)

    debug = partialmethod(_log, level="debug")
    success = partialmethod(_log, level=LogLevelChoices.LOG_SUCCESS)
    info = partialmethod(_log, level=LogLevelChoices.LOG_INFO)
    warning = partialmethod(_log, level=LogLevelChoices.LOG_WARNING)
    failure = partialmethod(_log, level=LogLevelChoices.LOG_FAILURE)

    def log_exception(self, exc_value, exc_type=None, exc_traceback=None):
        exc_traceback = exc_traceback or exc_value.__traceback__
        exc_type = exc_type or type(exc_value)
        stacktrace = "".join(tb.format_tb(exc_traceback))
        self.failure(f"Unhandled error occured: `{exc_type}: {exc_value}`\n```\n{stacktrace}\n```")

    def flush(self):
        self._script_id = None
        self.messages = []
