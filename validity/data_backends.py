from contextlib import contextmanager
from itertools import chain, groupby
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from netbox.registry import registry

from validity import config
from validity.models import VDevice
from .pollers.result import PollingInfo


if config.netbox_version >= 3.7:
    from netbox.data_backends import DataBackend
else:
    from core.data_backends import DataBackend


class PollingBackend(DataBackend):
    """
    Custom Data Source Backend to poll devices
    """

    name = "device_polling"
    label = _("Device Polling")

    parameters = {
        "datasource_id": forms.IntegerField(
            label=_("Data Source ID"),
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )
    }

    devices_qs = VDevice.objects.prefetch_poller(with_commands=True).annotate_datasource_id().order_by("poller_id")
    metainfo_file = Path("polling_info.yaml")

    def bound_devices_qs(self, device_filter: Q):
        datasource_id = self.params.get("datasource_id")
        assert datasource_id, 'Data Source parameters must contain "datasource_id"'
        return self.devices_qs.filter(data_source_id=datasource_id).filter(device_filter)

    def write_metainfo(self, dir_name: str, polling_info: PollingInfo) -> None:
        # NetBox does not provide an opportunity for a backend to return any info/errors to the user
        # Hence, it will be written into "polling_info.yaml" file
        path = dir_name / self.metainfo_file
        path.write_text(yaml.safe_dump(polling_info.model_dump(exclude_defaults=True), sort_keys=False))

    @contextmanager
    def fetch(self, device_filter: Q | None = None):
        with TemporaryDirectory() as dir_name:
            devices = self.bound_devices_qs(device_filter or Q())
            result_generators = [
                poller.get_backend().poll(device_group)
                for poller, device_group in groupby(devices, key=lambda device: device.poller)
            ]
            errors = set()
            for cmd_result in chain.from_iterable(result_generators):
                if cmd_result.errored:
                    errors.add(cmd_result.descriptive_error)
                cmd_result.write_on_disk(dir_name)
            polling_info = PollingInfo(
                devices_polled=devices.count(), errors=errors, partial_sync=device_filter is not None
            )
            self.write_metainfo(dir_name, polling_info)
            yield dir_name


backends = [PollingBackend]

if config.netbox_version < 3.7:
    # "register" DS backend manually via monkeypatch
    from core.choices import DataSourceTypeChoices
    from core.forms import DataSourceForm
    from core.models import DataSource

    registry["data_backends"][PollingBackend.name] = PollingBackend
    DataSourceTypeChoices._choices += [(PollingBackend.name, PollingBackend.label)]
    DataSourceForm.base_fields["type"] = DataSource._meta.get_field("type").formfield()
