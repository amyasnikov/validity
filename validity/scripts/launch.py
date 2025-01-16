import uuid
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable

from core.choices import JobStatusChoices
from core.models import Job
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django_rq.queues import DjangoRQ, get_redis_connection
from redis import Redis
from rq import Queue, Worker
from rq.job import Job as RQJob

from .data_models import FullScriptParams, ScriptParams, Task


@dataclass
class LauncherFactory:
    django_rq_config: dict[str, Any]

    def get_connection(self) -> Redis:
        return get_redis_connection(self.django_rq_config)

    def get_queue(self, queue_name: str) -> Queue:
        is_async = self.django_rq_config.get("ASYNC", True)
        default_timeout = self.django_rq_config.get("DEFAULT_TIMEOUT")
        return DjangoRQ(
            queue_name,
            default_timeout=default_timeout,
            connection=self.get_connection(),
            is_async=is_async,
            job_class=RQJob,
        )

    def worker_count_fn(self) -> Callable[[Queue], int]:
        return lambda queue: Worker.count(self.get_connection(), queue)

    def get_launcher(
        self, job_name: str, job_object_factory: Callable[[ScriptParams], Model], tasks: list[Task], queue_name: str
    ) -> "Launcher":
        queue = self.get_queue(queue_name)
        return Launcher(job_name, job_object_factory, tasks, rq_queue=queue, worker_count_fn=self.worker_count_fn())


@dataclass
class Launcher:
    job_name: str
    job_object_factory: Callable[[ScriptParams], Model]
    tasks: list[Task]
    rq_queue: Queue
    worker_count_fn: Callable[[Queue], int]

    @property
    def has_workers(self) -> bool:
        return self.worker_count_fn(self.rq_queue) > 0

    def _create_netbox_job(self, params: ScriptParams) -> Job:
        status = JobStatusChoices.STATUS_SCHEDULED if params.schedule_at else JobStatusChoices.STATUS_PENDING
        obj = self.job_object_factory(params)
        content_type = ContentType.objects.get_for_model(type(obj))
        return Job.objects.create(
            object_type=content_type,
            object_id=obj.pk,
            name=self.job_name,
            status=status,
            scheduled=params.schedule_at,
            interval=params.schedule_interval,
            user=params.request.get_user(),
            job_id=uuid.uuid4(),
        )

    def _enqueue(self, params: FullScriptParams, rq_job_id: uuid.UUID) -> None:
        prev_job = None
        for task_idx, task in enumerate(self.tasks):
            enqueue_fn = (
                partial(self.rq_queue.enqueue_at, params.schedule_at)
                if params.schedule_at and task_idx == 0
                else self.rq_queue.enqueue
            )
            task_kwargs = task.as_kwargs | {"depends_on": prev_job, "params": params}
            if task_idx == len(self.tasks) - 1:
                task_kwargs["job_id"] = str(rq_job_id)  # job id of the last task matches with the job id from the DB
            prev_job = (
                [enqueue_fn(**task_kwargs, worker_id=worker_id) for worker_id in range(params.workers_num)]
                if task.multi_workers
                else enqueue_fn(**task_kwargs)
            )

    def __call__(self, params: ScriptParams) -> Job:
        nb_job = self._create_netbox_job(params)
        full_params = params.with_job_info(nb_job)
        self._enqueue(full_params, nb_job.job_id)
        return nb_job
