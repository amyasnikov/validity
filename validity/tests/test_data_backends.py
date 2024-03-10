from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import yaml

from validity.data_backends import PollingBackend
from validity.pollers.result import PollingInfo


def test_write_metainfo():
    with TemporaryDirectory() as dir_name:
        backend = PollingBackend("/")
        polling_info = PollingInfo(devices_polled=5, errors=[])
        backend.write_metainfo(dir_name, polling_info)
        file = Path(dir_name) / "polling_info.yaml"
        assert yaml.safe_load(file.read_text()) == polling_info.model_dump(exclude_defaults=True)


def test_start_polling():
    def poll(devices, poller):
        poller.devices = list(devices)

    backend = PollingBackend("/")
    poller1 = Mock(name="poller1")
    poller1.get_backend.return_value.poll = partial(poll, poller=poller1)
    poller2 = Mock(name="poller2")
    poller2.get_backend.return_value.poll = partial(poll, poller=poller2)
    devices = [
        Mock(poller=poller1),
        Mock(poller=poller1),
        Mock(poller=poller2),
        Mock(poller=None),
        Mock(poller=None),
        Mock(poller=None),
    ]
    result_generators, errors = backend.start_polling(devices)
    assert len(result_generators) == 2
    assert poller1.devices == devices[:2]
    assert poller2.devices == devices[2:3]
    assert len(errors) == 3
    device_strings = {str(device): device for device in devices}
    for error in errors:
        assert device_strings[error.device].poller is None
