from functools import partial
from typing import TYPE_CHECKING, Annotated, Sequence

from dimi import Singleton

from validity import di
from .base import DevicePoller, ThreadPoller


if TYPE_CHECKING:
    from validity.models import Command


@di.dependency(scope=Singleton)
class PollerFactory:
    def __init__(
        self,
        poller_map: Annotated[dict, "poller_map"],
        max_threads: Annotated[int, "validity_settings.polling_threads"],
    ) -> None:
        self.poller_map = poller_map
        self.max_threads = max_threads

    def __call__(self, connection_type: str, credentials: dict, commands: Sequence["Command"]) -> DevicePoller:
        if poller_cls := self.poller_map.get(connection_type):
            if issubclass(poller_cls, ThreadPoller):
                poller_cls = partial(poller_cls, thread_workers=self.max_threads)
            return poller_cls(credentials=credentials, commands=commands)
        raise KeyError("No poller exists for this connection type", connection_type)
