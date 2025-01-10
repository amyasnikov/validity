import datetime
import operator
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from functools import reduce
from typing import Callable, ClassVar
from uuid import UUID

from core.models import Job
from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from pydantic import ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass as py_dataclass
from rq import Callback

from validity.models import ComplianceSelector
from validity.utils.logger import Message


##
# Common models
##


@dataclass
class RequestInfo:
    """
    Pickleable substitution for Django's HttpRequest
    """

    id: UUID
    user_id: int

    user_queryset: ClassVar[QuerySet] = get_user_model().objects.all()

    @classmethod
    def from_http_request(cls, request):
        return cls(id=request.id, user_id=request.user.pk)

    def get_user(self):
        return self.user_queryset.get(pk=self.user_id)


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


@py_dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True, populate_by_name=True))
class ScriptParams(ABC):
    request: RequestInfo
    schedule_at: datetime.datetime | None = Field(default=None, validation_alias="_schedule_at")
    schedule_interval: int | None = Field(default=None, validation_alias="_interval")
    workers_num: int = 1

    @field_validator("request", mode="before")
    @classmethod
    def coerce_request_info(cls, value):
        if not isinstance(value, (RequestInfo, dict)):
            value = RequestInfo.from_http_request(value)
        return value

    @abstractmethod
    def _full_cls(cls) -> type["FullScriptParams"]: ...

    def with_job_info(self, job: Job) -> "FullScriptParams":
        return self._full_cls()(**asdict(self) | {"job_id": job.pk, "object_id": job.object_id})


@py_dataclass(kw_only=True)
class FullScriptParams(ScriptParams):
    job_id: int
    object_id: int

    job_queryset: ClassVar[QuerySet[Job]] = Job.objects.all()

    def get_job(self):
        return self.job_queryset.get(pk=self.job_id)


##
# RunTests models
##


@dataclass(slots=True)
class SplitResult:
    log: list[Message]
    slices: list[dict[int, list[int]]]


@dataclass(slots=True, frozen=True)
class TestResultRatio:
    passed: int
    total: int

    def __add__(self, other):
        return type(self)(self.passed + other.passed, self.total + other.total)

    @property
    def serialized(self):
        return asdict(self)


@dataclass(slots=True)
class ExecutionResult:
    test_stat: TestResultRatio
    log: list[Message]
    errored: bool = False


@py_dataclass(kw_only=True)
class RunTestsParams(ScriptParams):
    sync_datasources: bool = False
    selectors: list[int] = field(default_factory=list)
    devices: list[int] = field(default_factory=list)
    test_tags: list[int] = field(default_factory=list)
    explanation_verbosity: int = 2
    overriding_datasource: int | None = None

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
        filtr = reduce(operator.or_, (selector.filter for selector in selectors.prefetch_filters()))
        if self.devices:
            filtr &= Q(pk__in=self.devices)
        return filtr

    def _full_cls(cls):
        return FullRunTestsParams


@py_dataclass(kw_only=True)
class FullRunTestsParams(FullScriptParams, RunTestsParams):
    pass


##
# BackUp models
##


@py_dataclass(kw_only=True)
class BackUpParams(ScriptParams):
    backuppoint_id: int

    def _full_cls(cls):
        return FullBackUpParams


@py_dataclass(kw_only=True)
class FullBackUpParams(FullScriptParams, BackUpParams):
    pass
