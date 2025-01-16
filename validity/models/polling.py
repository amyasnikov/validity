from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Any, Collection

from dcim.models import Device
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity import di
from validity.choices import CommandTypeChoices
from validity.fields import EncryptedDictField
from validity.managers import CommandQS, PollerQS
from validity.model_validators import commands_with_appropriate_type, only_one_config_command
from validity.subforms import CLICommandForm, CustomCommandForm, JSONAPICommandForm, NetconfCommandForm
from validity.utils.misc import LazyIterator
from .base import BaseModel, SubformMixin
from .serializer import Serializer


if TYPE_CHECKING:
    from validity.pollers.factory import PollerFactory


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
    subforms = {
        "CLI": CLICommandForm,
        "json_api": JSONAPICommandForm,
        "netconf": NetconfCommandForm,
        "custom": CustomCommandForm,
    }

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def get_type_color(self):
        return CommandTypeChoices.colors.get(self.type)


class Poller(BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    connection_type = models.CharField(
        _("Connection Type"), max_length=50, choices=LazyIterator(lambda: di["PollerChoices"].choices)
    )
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

    @di.inject
    def __init__(self, *args: Any, poller_factory: Annotated["PollerFactory", ...], **kwargs: Any) -> None:
        self._poller_factory = poller_factory
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    @property
    def credentials(self) -> dict:
        return self.public_credentials | self.private_credentials.decrypted

    def get_connection_type_color(self):
        return di["PollerChoices"].colors.get(self.connection_type)

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
        return self._poller_factory(self.connection_type, self.credentials, self.commands.all())

    @staticmethod
    def validate_commands(commands: Collection[Command], command_types: dict[str, list[str]], connection_type: str):
        commands_with_appropriate_type(commands, command_types, connection_type)
        only_one_config_command(commands)
