from contextlib import nullcontext, suppress
from dataclasses import dataclass
from typing import Annotated, Any, Callable

from dimi import Singleton

from validity import di
from validity.utils.orm import TwoPhaseTransaction
from ..data_models import FullRunTestsParams
from ..logger import Logger
from .base import AsFuncMixin, TracebackMixin


def rollback(transaction_id):
    TwoPhaseTransaction(transaction_id).rollback()


@di.dependency(scope=Singleton)
@dataclass(repr=False)
class RollbackWorker(AsFuncMixin, TracebackMixin):
    transaction_template: Annotated[str, "runtests_transaction_template"]
    rollback_func: Callable[[str], None] = rollback
    log_factory: Callable[[], Logger] = Logger

    def rollback(self, params: FullRunTestsParams, failed_worker_id: int) -> None:
        for worker_id in range(params.workers_num):
            transaction_id = self.transaction_template.format(job=params.job_id, worker=worker_id)
            suppressor = suppress(Exception) if worker_id == failed_worker_id else nullcontext()
            with suppressor:
                self.rollback_func(transaction_id)

    def __call__(self, job, connection, type, value, traceback) -> Any:
        script_params = job.kwargs["params"]
        failed_worker_id = job.kwargs["worker_id"]
        self.rollback(script_params, failed_worker_id)
        self.terminate_job(script_params.get_job(), type, value, traceback)
