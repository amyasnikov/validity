import logging
import traceback as tb
from functools import partialmethod

from extras.choices import LogLevelChoices

from .data_models import Message


logger = logging.getLogger("validity.scripts")


class Logger:
    """
    Collects the logs in the format of NetBox Custom Script
    """

    def __init__(self, script_id: str | None = None) -> None:
        self.messages = []
        self.script_id = script_id

    def _log(self, message: str, level: LogLevelChoices):
        msg = Message(level, message, script_id=self.script_id)
        self.messages.append(msg)
        logger.log(LogLevelChoices.SYSTEM_LEVELS[level], message)

    debug = partialmethod(_log, level=LogLevelChoices.LOG_DEBUG)
    success = partialmethod(_log, level=LogLevelChoices.LOG_SUCCESS)
    info = partialmethod(_log, level=LogLevelChoices.LOG_INFO)
    warning = partialmethod(_log, level=LogLevelChoices.LOG_WARNING)
    failure = partialmethod(_log, level=LogLevelChoices.LOG_FAILURE)

    def log_exception(self, exc_value, exc_type=None, exc_traceback=None):
        exc_traceback = exc_traceback or exc_value.__traceback__
        exc_type = exc_type or type(exc_value)
        stacktrace = "".join(tb.format_tb(exc_traceback))
        self.failure(f"Unhandled error occured: `{exc_type}: {exc_value}`\n```\n{stacktrace}\n```")
