from typing import TYPE_CHECKING, Annotated, Sequence

from dimi import Singleton

from validity import di
from validity.settings import PollerInfo
from validity.utils.misc import partialcls
from .base import BasePoller, ThreadPoller


if TYPE_CHECKING:
    from validity.models import Command


@di.dependency(scope=Singleton)
class PollerChoices:
    def __init__(self, pollers_info: Annotated[list[PollerInfo], "pollers_info"]):
        self.choices: list[tuple[str, str]] = []
        self.classes: dict[str, type] = {}
        self.colors: dict[str, str] = {}
        self.command_types: dict[str, Sequence[str]] = {}

        for info in pollers_info:
            self.choices.append((info.name, info.verbose_name))
            self.classes[info.name] = info.klass
            self.colors[info.name] = info.color
            self.command_types[info.name] = info.command_types


@di.dependency(scope=Singleton)
class PollerFactory:
    def __init__(
        self,
        poller_map: Annotated[dict[str, type[BasePoller]], "PollerChoices.classes"],
        max_threads: Annotated[int, "validity_settings.polling_threads"],
    ) -> None:
        self.poller_map = poller_map
        self.max_threads = max_threads

    def __call__(self, connection_type: str, credentials: dict, commands: Sequence["Command"]) -> BasePoller:
        if poller_cls := self.poller_map.get(connection_type):
            if issubclass(poller_cls, ThreadPoller):
                poller_cls = partialcls(poller_cls, thread_workers=self.max_threads)
            return poller_cls(credentials=credentials, commands=commands)
        raise KeyError("No poller exists for this connection type", connection_type)
