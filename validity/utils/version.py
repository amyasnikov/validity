import operator
from functools import total_ordering


@total_ordering
class NetboxVersion:
    def __init__(self, version: str | float | int) -> None:
        version = str(version)
        version, *suffix = version.split("-", maxsplit=1)
        splitted_version = [int(i) for i in version.split(".")]
        while len(splitted_version) < 3:
            splitted_version.append(0)
        if suffix:
            splitted_version.append(suffix[0])
        self.version = tuple(splitted_version)

    def _compare(self, operator_, other):
        if isinstance(other, type(self)):
            return operator_(self.version, other.version)
        return operator_(self.version, type(self)(other).version)

    def __eq__(self, other) -> bool:
        return self._compare(operator.eq, other)

    def __lt__(self, other) -> bool:
        return self._compare(operator.lt, other)

    def __str__(self) -> str:
        return ".".join(str(i) for i in self.version)

    def __repr__(self) -> str:
        return f"NetboxVersion({str(self)})"
