from typing import TYPE_CHECKING, Sequence

from validity.choices import ConnectionTypeChoices
from .base import DevicePoller
from .cli import NetmikoPoller


if TYPE_CHECKING:
    from validity.models import Command


class PollerFactory:
    def __init__(self, poller_map: dict) -> None:
        self.poller_map = poller_map

    def __call__(self, connection_type: str, credentials: dict, commands: Sequence["Command"]) -> DevicePoller:
        if poller_cls := self.poller_map.get(connection_type):
            return poller_cls(credentials=credentials, commands=commands)
        raise KeyError("No poller exist for this connection type", connection_type)


get_poller = PollerFactory(poller_map={ConnectionTypeChoices.netmiko: NetmikoPoller})
