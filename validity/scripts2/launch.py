import datetime
import uuid
from dataclasses import dataclass
from functools import partial
from typing import Callable

import django_rq
from core.choices import JobStatusChoices
from core.models import Job
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from rq import Callback, Queue
from utilities.rqworker import get_queue_for_model

from validity import settings
from validity.models import ComplianceReport
from . import steps
from .data_models import FullScriptParams, ScriptParams, Task


@dataclass
class Launcher:
    job_name: str
    job_object_model: type[Model]
    get_queue_fn: Callable[[str], Queue]
    tasks: list[Task]

    @property
    def rq_queue(self) -> Queue:
        return self.get_queue_fn(self.job_object_model._meta.model_name)

    def create_netbox_job(
        self, schedule_at: datetime.datetime | None, interval: int | None, user: AbstractBaseUser
    ) -> Job:
        status = JobStatusChoices.STATUS_SCHEDULED if schedule_at else JobStatusChoices.STATUS_PENDING
        obj = self.job_object_model.objects.create()
        content_type = ContentType.objects.get_for_model(self.job_object_model)
        return Job.objects.create(
            object_type=content_type.pk,
            object_id=obj.pk,
            name=self.job_name,
            status=status,
            scheduled=schedule_at,
            interval=interval,
            user=user,
            job_id=uuid.uuid4(),
        )

    def enqueue(self, params: FullScriptParams, rq_job_id: uuid.UUID) -> None:
        enqueue_fn = (
            partial(self.rq_queue.enqueue_at, params.schedule_at) if params.schedule_at else self.rq_queue.enqueue
        )
        prev_job = None
        for task_idx, task in enumerate(self.tasks):
            task_kwargs = task.as_kwargs | {"depends_on": prev_job, "params": params}
            if task_idx == len(self.tasks) - 1:
                task_kwargs["job_id"] = rq_job_id
            prev_job = (
                [enqueue_fn(**task_kwargs, worker_id=worker_id) for worker_id in range(params.workers_num)]
                if task.multi_workers
                else enqueue_fn(**task_kwargs)
            )

    def __call__(self, params: ScriptParams):
        nb_job = self.create_netbox_job(params.schedule_at, params.schedule_interval, params.request.user)
        full_params = params.with_job_info(nb_job)
        self.enqueue(full_params, nb_job.job_id)


launch_tests = Launcher(
    job_name="RunTests",
    job_object_model=ComplianceReport,
    get_queue_fn=lambda model: django_rq.get_queue(get_queue_for_model(model)),
    tasks=[
        Task(steps.split_work, job_timeout=settings.worker_timeouts.split),
        Task(
            steps.execute_tests,
            job_timeout=settings.worker_timeouts.apply,
            on_failure=Callback(steps.rollback_test_results, timeout=settings.worker_timeouts.rollback),
            multi_workers=True,
        ),
        Task(steps.combine_work, job_timeout=settings.worker_timeouts.combine),
    ],
)
