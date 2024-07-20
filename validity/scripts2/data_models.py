import datetime
import operator
from dataclasses import asdict, dataclass, field
from functools import reduce
from typing import Callable, ClassVar

from core.models import Job
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from extras.choices import LogLevelChoices
from pydantic import BaseModel
from rq import Callback

from validity.models import ComplianceSelector


@dataclass(slots=True, frozen=True)
class Message:
    status: LogLevelChoices
    message: str
    time: datetime.datetime = field(default_factory=timezone.now)
    script_id: str | None = None

    @property
    def serialized(self) -> dict:
        msg = self.message
        if self.script_id:
            msg = f"{self.script_id}: {msg}"
        return {"status": self.status, "message": msg, "time": self.time.isoformat()}


@dataclass(slots=True)
class SplitResult:
    log: list[Message]
    slices: list[dict[int, list[int]]]


@dataclass(slots=True, frozen=True)
class TestResultRatio:
    passed: int
    total: int

    def __add__(self, other):
        return type(self)(self.passed + other.passed, self.total + other.overall)

    @property
    def serialized(self):
        return asdict(self)


@dataclass(slots=True)
class ExecutionResult:
    test_stat: TestResultRatio
    log: list[Message]


class ScriptParams(BaseModel):
    sync_datasources: bool = False
    selectors: list[int] = []
    devices: list[int] = []
    test_tags: list[int] = []
    explanation_verbosity: int = 2
    override_datasource: int | None = None
    workers_num: int = 1

    schedule_at: datetime.datetime | None = None
    schedule_interval: int | None = None
    request: HttpRequest

    @property
    def selector_qs(self) -> QuerySet[ComplianceSelector]:
        qs = (
            ComplianceSelector.objects.filter(pk__in=self.selectors)
            if self.selectors
            else ComplianceSelector.objects.all()
        )
        if self.test_tags:
            qs = qs.filter(tests__tags__pk__in=self.test_tags).distinct()
        return qs

    def get_device_filter(self) -> Q:
        selectors = self.selector_qs
        if not selectors.exists():
            return Q(pk__in=[])
        filtr = reduce(operator.or_, (selector.filter for selector in selectors))
        if self.devices:
            filtr &= Q(pk__in=self.devices)
        return filtr

    def with_job_info(self, job: Job) -> "FullScriptParams":
        return FullScriptParams(**self.model_dump(), job_id=job.pk, report_id=job.object_id)


class FullScriptParams(ScriptParams):
    job_id: int
    report_id: int

    job_queryset: ClassVar[QuerySet[Job]] = Job.objects.all()

    def get_job(self):
        return self.job_queryset.get(pk=self.job_id)


@dataclass
class Task:
    """
    Represents all the kwargs that can be passed to rq.Queue.enqueue
    """

    func: Callable
    job_timeout: int | str
    on_failure: Callback | None = None
    multi_workers: bool = False

    @property
    def as_kwargs(self):
        return {"f": self.func, "job_timeout": self.job_timeout, "on_failure": self.on_failure}