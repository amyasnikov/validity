from dataclasses import dataclass, field
from functools import cached_property

from rq.job import Job, get_current_job


@dataclass
class JobExtractor:
    nesting_level: int = 0
    _job: Job | None = field(default_factory=get_current_job)

    @property
    def nesting_name(self) -> str:
        if self.nesting_level == 0:
            return "Current"
        if self.nesting_level == 1:
            return "Parent"
        return f"x{self.nesting_level} Parent"

    @property
    def job(self) -> Job:
        if self._job is None:
            raise ValueError(f"{self.nesting_name} Job must not be None")
        return self._job

    @cached_property
    def parents(self) -> list["JobExtractor"]:
        result = [self._get_parent(dep) for dep in self.job.fetch_dependencies()]
        if result:
            self.__dict__["parent"] = result[0]
        return result

    @cached_property
    def parent(self) -> "JobExtractor":
        return self._get_parent(self.job.dependency)

    def _get_parent(self, dependency: Job | None) -> "JobExtractor":
        return type(self)(nesting_level=self.nesting_level + 1, _job=dependency)
