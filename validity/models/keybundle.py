from dcim.models import Device
from django.db import models
from django.utils.translation import gettext_lazy as _

from validity.choices import ConnectionTypeChoices
from validity.utils.dbfields import EncryptedDictField
from .base import BaseModel


class KeyBundle(BaseModel):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    connection_type = models.CharField(_("Connection Type"), max_length=50, choices=ConnectionTypeChoices.choices)
    public_credentials = models.JSONField(_("Public Credentials"), default=dict, blank=True)
    private_credentials = EncryptedDictField(_("Private Credentials"), blank=True)

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

        return VDevice.objects.annotate_keybundle_id().filter(keybundle_id=self.pk)

    def serialize_object(self):
        private_creds = self.private_credentials
        self.private_credentials = self.private_credentials.encrypted
        result = super().serialize_object()
        self.private_credentials = private_creds
        return result
