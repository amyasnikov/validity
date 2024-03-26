from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Optional

from django.utils.translation import gettext_lazy as _

from validity.compliance.serialization import Serializable
from validity.utils.misc import reraise
from .exceptions import NoComponentError, SerializationError, StateKeyError


if TYPE_CHECKING:
    from validity.models import Command


@dataclass(frozen=True)
class StateItem(Serializable):
    command: Optional["Command"]

    @classmethod
    def from_command(cls, command: "Command"):
        return cls(data_file=command.data_file, serializer=command.serializer, command=command)

    @property
    def contains_config(self) -> bool:
        return self.command is None or self.command.retrieves_config

    @property
    def name(self) -> str:
        return "config" if self.contains_config else self.command.label

    @property
    def verbose_name(self) -> str:
        return _("Config") if self.contains_config else self.command.name

    @property
    def error(self) -> SerializationError | None:
        try:
            self.serialized  # noqa: B018
            return
        except SerializationError as exc:
            return exc

    @property
    def serialized(self):
        try:
            return super().serialized
        except NoComponentError as exc:
            exc.parent = self.name
            raise


class State(dict):
    def __init__(self, items, config_command_label: str | None = None):
        super().__init__(items)
        self.config_command_label = config_command_label

    @classmethod
    def from_commands(cls, commands: Iterable["Command"]):
        items = []
        config_label = None
        for command in commands:
            if command.retrieves_config:
                config_label = command.label
            items.append(StateItem.from_command(command))
        return cls(((item.name, item) for item in items), config_label)

    def with_config(self, serializable: Serializable):
        state_item = StateItem(serializer=serializable.serializer, data_file=serializable.data_file, command=None)
        with suppress(SerializationError):
            state_item.serialized  # noqa: B018
            super().__setitem__("config", state_item)
            self.config_command_label = None
        return self

    def _blocked_op(self, *_):
        raise AttributeError("State is read only")

    __setitem__ = __delitem__ = pop = popitem = update = setdefault = clear = _blocked_op

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        if self.config_command_label and key == self.config_command_label:
            key = "config"
        with reraise(KeyError, StateKeyError):
            state_item = super().__getitem__(key)
        return state_item.serialized

    def get(self, key, default=None, ignore_errors=False):
        with suppress(Exception if ignore_errors else KeyError):
            return self[key]
        return default

    def get_full_item(self, key, default=None):
        return super().get(key, default)
