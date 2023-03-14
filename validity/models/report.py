from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Collection

from validity.managers import ComplianceReportQS
from .base import BaseReadOnlyModel


if TYPE_CHECKING:
    from validity.models import ComplianceTestResult


@dataclass(slots=True, kw_only=True)
class ResultStat:
    total: int = field(init=False, default=0)
    passed: int = field(init=False, default=0)

    def passed_percentage(self) -> float:
        if self.total == 0:
            return 100.0
        return round(self.passed / self.total, 1)


@dataclass(slots=True)
class ResultBatch(ResultStat):
    results: Collection["ComplianceTestResult"]
    low: ResultStat = field(init=False, default_factory=ResultStat)
    middle: ResultStat = field(init=False, default_factory=ResultStat)
    high: ResultStat = field(init=False, default_factory=ResultStat)

    def __post_init__(self):
        for result in self.results:
            self.total += 1
            result_stat = getattr(self, result.test.severity.lower())
            result_stat.total += 1
            if result.passed:
                self.passed += 1
                result_stat.passed += 1


class ComplianceReport(BaseReadOnlyModel):
    objects = ComplianceReportQS.as_manager()

    class Meta:
        ordering = ("-created",)

    def __str__(self) -> str:
        return f"report-{self.pk}"
