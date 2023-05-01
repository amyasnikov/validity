from dcim.models import Device

from validity.models import VDevice


def config(device: Device) -> dict | list | None:
    vdevice = VDevice()
    vdevice.__dict__ = device.__dict__.copy()
    return vdevice.config
