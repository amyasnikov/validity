from contextlib import contextmanager
from functools import cached_property
from typing import Iterable

from dcim.models import Device
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import CommandTypeChoices, ConnectionTypeChoices
from validity.managers import PollerQS
from validity.pollers import get_poller
from validity.subforms import CLICommandForm
from validity.utils.dbfields import EncryptedDictField
from .base import BaseModel, SubformMixin


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
            )
        ],
    )
    retrieves_config = models.BooleanField(
        _("Retrieves Configuration"),
        default=False,
        help_text=_("There can be only one command to retrieve configuration within each poller"),
    )
    type = models.CharField(_("Type"), max_length=50, choices=CommandTypeChoices.choices)
    parameters = models.JSONField(_("Parameters"))

    subform_type_field = "type"
    subform_json_field = "parameters"
    subforms = {"CLI": CLICommandForm}

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def get_type_color(self):
        return CommandTypeChoices.colors.get(self.type)


class Poller(BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    connection_type = models.CharField(_("Connection Type"), max_length=50, choices=ConnectionTypeChoices.choices)
    public_credentials = models.JSONField(_("Public Credentials"), default=dict, blank=True)
    private_credentials = EncryptedDictField(_("Private Credentials"), blank=True)
    commands = models.ManyToManyField(Command, verbose_name=_("Commands"), related_name="pollers")

    objects = PollerQS.as_manager()

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    @property
    def credentials(self):
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

    def serialize_object(self):
        with self.serializable_credentials():
            return super().serialize_object()

    @contextmanager
    def serializable_credentials(self):
        private_creds = self.private_credentials
        try:
            self.private_credentials = self.private_credentials.encrypted
            yield
        finally:
            self.private_credentials = private_creds

    @staticmethod
    def validate_commands(commands: Iterable[Command]):
        config_commands_count = sum(1 for cmd in commands if cmd.retrieves_config)
        if config_commands_count > 1:
            raise ValidationError(
                {
                    "commands": _(
                        "No more than 1 command to retrieve config is allowed, "
                        f"but {config_commands_count} were specified"
                    )
                }
            )
