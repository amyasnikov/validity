from functools import cached_property
from typing import Collection

from dcim.models import Device
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import CommandTypeChoices, ConnectionTypeChoices
from validity.fields import EncryptedDictField
from validity.managers import CommandQS, PollerQS
from validity.pollers import get_poller
from validity.subforms import CLICommandForm, JSONAPICommandForm, NetconfCommandForm
from .base import BaseModel, SubformMixin
from .serializer import Serializer


class Command(SubformMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    label = models.CharField(
        _("Label"),
        max_length=100,
        unique=True,
        help_text=_("String key to access command output inside Tests"),
        validators=[
            RegexValidator(
                regex="^[a-z][a-z0-9_]*$",
                message=_("Only lowercase ASCII letters, numbers and underscores are allowed"),
            ),
            RegexValidator(regex="^config$", message=_("This label name is reserved"), inverse_match=True),
        ],
    )
    retrieves_config = models.BooleanField(
        _("Retrieves Configuration"),
        default=False,
        help_text=_("There can be only one command to retrieve configuration within each poller"),
    )
    serializer = models.ForeignKey(
        Serializer,
        on_delete=models.CASCADE,
        verbose_name=_("Serializer"),
        related_name="commands",
        null=True,
        blank=True,
    )
    type = models.CharField(_("Type"), max_length=50, choices=CommandTypeChoices.choices)
    parameters = models.JSONField(_("Parameters"))

    objects = CommandQS.as_manager()

    subform_type_field = "type"
    subform_json_field = "parameters"
    subforms = {"CLI": CLICommandForm, "json_api": JSONAPICommandForm, "netconf": NetconfCommandForm}

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def get_type_color(self):
        return CommandTypeChoices.colors.get(self.type)


class Poller(BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    connection_type = models.CharField(_("Connection Type"), max_length=50, choices=ConnectionTypeChoices.choices)
    public_credentials = models.JSONField(
        _("Public Credentials"),
        default=dict,
        blank=True,
        help_text=_("Enter non-private parameters of the connection type in JSON format."),
    )
    private_credentials = EncryptedDictField(
        _("Private Credentials"),
        blank=True,
        help_text=_(
            "Enter private parameters of the connection type in JSON format. "
            "All the values are going to be encrypted."
        ),
    )
    commands = models.ManyToManyField(Command, verbose_name=_("Commands"), related_name="pollers")

    objects = PollerQS.as_manager()

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    @property
    def credentials(self) -> dict:
        return self.public_credentials | self.private_credentials.decrypted

    def get_connection_type_color(self):
        return ConnectionTypeChoices.colors.get(self.connection_type)

    @property
    def bound_devices(self) -> models.QuerySet[Device]:
        from .device import VDevice

        return VDevice.objects.annotate_poller_id().filter(poller_id=self.pk)

    @cached_property
    def config_command(self) -> Command | None:
        """
        Bound command which is responsible for retrieving configuration
        """
        return next((cmd for cmd in self.commands.all() if cmd.retrieves_config), None)

    def get_backend(self):
        return get_poller(self.connection_type, self.credentials, self.commands.all())

    @staticmethod
    def validate_commands(connection_type: str, commands: Collection[Command]):
        # All the commands must be of the matching type
        conn_type = ConnectionTypeChoices[connection_type]
        if any(cmd.type != conn_type.acceptable_command_type for cmd in commands):
            raise ValidationError(
                {
                    "commands": _("%(conntype)s accepts only %(cmdtype)s commands")
                    % {"conntype": conn_type.label, "cmdtype": conn_type.acceptable_command_type.label}
                }
            )

        # Only one bound "retrives config" command may exist
        config_commands_count = sum(1 for cmd in commands if cmd.retrieves_config)
        if config_commands_count > 1:
            raise ValidationError(
                {
                    "commands": _("No more than 1 command to retrieve config is allowed, but %(cnt)s were specified")
                    % {"cnt": config_commands_count}
                }
            )
