import datetime
import operator
from dataclasses import asdict, dataclass, field
from functools import cached_property, reduce

from django.db.models import Q, QuerySet
from django.utils import timezone
from extras.choices import LogLevelChoices
from pydantic import BaseModel

from validity.models import ComplianceSelector


@dataclass(slots=True, frozen=True)
class Message:
    status: LogLevelChoices
    message: str
    time: datetime.datetime = field(default_factory=timezone.now)
    script_id: str | None = None

    @property
    def serialized(self) -> dict:  # delete this if not needed
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

    @cached_property
    def device_filter(self) -> Q:
        selectors = self.selector_qs
        if not selectors.exists():
            return Q(pk__in=[])
        filtr = reduce(operator.or_, (selector.filter for selector in selectors))
        if self.devices:
            filtr &= Q(pk__in=self.devices)
        return filtr
