import inspect
from contextlib import nullcontext, suppress
from dataclasses import dataclass
from typing import Any, Callable

from validity.utils.orm import TwoPhaseTransaction
from ..data_models import FullScriptParams
from ..logger import Logger
from .apply import execute_tests
from .base import TracebackMixin


@dataclass
class RollbackWorker(TracebackMixin):
    transaction_template: str
    rollback_func: Callable[[str], None]
    log_factory: Callable[[], Logger]

    def rollback(self, params: FullScriptParams, failed_worker_id: int) -> None:
        for worker_id in range(params.workers_num):
            transaction_id = self.transaction_template.format(job=params.job_id, worker=worker_id)
            suppressor = suppress(Exception) if worker_id == failed_worker_id else nullcontext()
            with suppressor:
                self.rollback_func(transaction_id)

    def __call__(self, job, connection, type, value, traceback) -> Any:
        apply_arguments = inspect.signature(execute_tests).bind(*job.args, **job.kwargs).arguments
        script_params = apply_arguments["params"]
        failed_worker_id = apply_arguments["worker_id"]
        self.rollback(script_params, failed_worker_id)
        job = apply_arguments["params"].get_job()
        self.terminate_job(job, type, value, traceback)


rollback_test_results = RollbackWorker(
    transaction_template=execute_tests.transaction_template,
    rollback_func=lambda transaction_id: TwoPhaseTransaction(transaction_id).rollback(),
    log_factory=Logger,
)
