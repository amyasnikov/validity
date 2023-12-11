from dcim.models import Device
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import CommandTypeChoices, ConnectionTypeChoices
from validity.subforms import CLICommandForm
from validity.utils.dbfields import EncryptedDictField
from .base import BaseModel, SubformMixin


class Command(SubformMixin, BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    retrieves_config = models.BooleanField(
        _("Retrieves Configuration"),
        default=False,
        help_text=_("There can be only one command to retrieve configuration within each poller"),
    )
    type = models.CharField(_("Type"), max_length=50, choices=CommandTypeChoices.choices)
    parameters = models.JSONField(_("Parameters"))

    clone_fields = ("retrieves_config", "type", "parameters")
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

    clone_fields = ("connection_type", "public_credentials", "private_credentials")

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

    def serialize_object(self):
        private_creds = self.private_credentials
        self.private_credentials = self.private_credentials.encrypted
        result = super().serialize_object()
        self.private_credentials = private_creds
        return result
