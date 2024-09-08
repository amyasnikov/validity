import datetime
import uuid
from dataclasses import dataclass
from functools import partial
from typing import Callable

from core.choices import JobStatusChoices
from core.models import Job
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from rq import Queue

from .data_models import FullScriptParams, ScriptParams, Task


@dataclass
class Launcher:
    job_name: str
    job_object_factory: Callable[[], Model]
    rq_queue: Queue
    tasks: list[Task]

    def create_netbox_job(
        self, schedule_at: datetime.datetime | None, interval: int | None, user: AbstractBaseUser
    ) -> Job:
        status = JobStatusChoices.STATUS_SCHEDULED if schedule_at else JobStatusChoices.STATUS_PENDING
        obj = self.job_object_factory()
        content_type = ContentType.objects.get_for_model(type(obj))
        return Job.objects.create(
            object_type=content_type,
            object_id=obj.pk,
            name=self.job_name,
            status=status,
            scheduled=schedule_at,
            interval=interval,
            user=user,
            job_id=uuid.uuid4(),
        )

    def enqueue(self, params: FullScriptParams, rq_job_id: uuid.UUID) -> None:
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
        nb_job = self.create_netbox_job(params.schedule_at, params.schedule_interval, params.request.get_user())
        full_params = params.with_job_info(nb_job)
        self.enqueue(full_params, nb_job.job_id)
        return nb_job
