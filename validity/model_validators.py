from typing import TYPE_CHECKING, Collection

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


if TYPE_CHECKING:
    from validity.models import Command


def only_one_config_command(commands: Collection["Command"]) -> None:
    config_commands_count = sum(1 for cmd in commands if cmd.retrieves_config)
    if config_commands_count > 1:
        raise ValidationError(
            {
                "commands": _("No more than 1 command to retrieve config is allowed, but %(cnt)s were specified")
                % {"cnt": config_commands_count}
            }
        )


def commands_with_appropriate_type(
    commands: Collection["Command"], command_types: dict[str, list[str]], connection_type: str
):
    acceptable_command_types = command_types.get(connection_type, [])
    if invalid_cmds := [cmd.label for cmd in commands if cmd.type not in acceptable_command_types]:
        raise ValidationError(
            {
                "commands": _(
                    "The following commands have inappropriate type and cannot be bound to this Poller: %(cmds)s"
                )
                % {"cmds": ", ".join(label for label in invalid_cmds)}
            }
        )
