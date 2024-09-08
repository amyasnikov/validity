from typing import Sequence

from core.choices import JobStatusChoices

from .data_models import Message


class AbortScript(Exception):
    def __init__(self, *args, status: str = JobStatusChoices.STATUS_FAILED, logs: Sequence[Message] = ()) -> None:
        self.status = status
        self.logs = logs
        super().__init__(*args)
