import uuid
from dataclasses import asdict
from unittest.mock import Mock

import pytest
from core.models import Job
from django.utils import timezone
from factories import UserFactory

from validity.models import ComplianceReport
from validity.scripts.data_models import RequestInfo, ScriptParams, Task
from validity.scripts.launch import Launcher


class ConcreteScriptParams(ScriptParams):
    def with_job_info(self, job: Job):
        return FullParams(**asdict(self) | {"job": job})


class FullParams:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs.copy()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


@pytest.fixture
def launcher(db):
    report = ComplianceReport.objects.create()
    return Launcher(job_name="test_launcher", job_object_factory=lambda: report, rq_queue=Mock(), tasks=[])


@pytest.fixture
def params(db):
    user = UserFactory()
    return ConcreteScriptParams(request=RequestInfo(id=uuid.uuid4(), user_id=user.pk), workers_num=1)


@pytest.mark.parametrize("schedule_at", [None, timezone.now()])
@pytest.mark.django_db
def test_launcher(launcher, params, schedule_at):
    def task_func(): ...

    params.schedule_at = schedule_at
    launcher.tasks = [Task(task_func, job_timeout=60)]
    job = launcher(params)
    assert isinstance(job, Job) and job.object == launcher.job_object_factory()
    enqueue_fn = getattr(launcher.rq_queue, "enqueue_at" if schedule_at else "enqueue")
    enqueue_fn.assert_called_once()
    enqueue_kwargs = enqueue_fn.call_args.kwargs
    assert enqueue_kwargs["job_id"] == str(job.job_id)
    assert enqueue_kwargs["params"] == params.with_job_info(job)
    assert enqueue_kwargs["f"] == task_func
    assert enqueue_kwargs["job_timeout"] == 60
    assert enqueue_kwargs["depends_on"] is None


@pytest.mark.django_db
def test_multi_tasks(launcher, params):
    def task_func_1(): ...
    def task_func_2(): ...

    params.workers_num = 3
    launcher.tasks = [Task(task_func_1, job_timeout=10, multi_workers=True), Task(task_func_2, job_timeout=20)]
    launcher(params)
    assert launcher.rq_queue.enqueue.call_count == 4
    assert launcher.rq_queue.enqueue.call_args.kwargs["depends_on"] == [launcher.rq_queue.enqueue.return_value] * 3
