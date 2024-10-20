import time
from unittest.mock import MagicMock, Mock

import pytest

from validity.pollers import NetmikoPoller, RequestsPoller
from validity.pollers.factory import PollerChoices
from validity.pollers.http import HttpDriver
from validity.settings import PollerInfo


class TestNetmikoPoller:
    @pytest.fixture
    def get_mocked_poller(self, monkeypatch):
        def _get_poller(credentials, commands, mock):
            monkeypatch.setattr(NetmikoPoller, "driver_factory", mock)
            return NetmikoPoller(credentials, commands)

        return _get_poller

    @pytest.fixture
    def get_mocked_device(self):
        def _get_device(primary_ip):
            db_ip = Mock(address=Mock(ip=primary_ip))
            return Mock(primary_ip=db_ip)

        return _get_device

    @pytest.mark.django_db
    def test_get_driver(self, get_mocked_poller, get_mocked_device):
        credentials = {"user": "admin", "password": "1234"}
        poller = get_mocked_poller(credentials, [], Mock())
        device = get_mocked_device("1.1.1.1")
        assert poller.get_credentials(device) == credentials | {poller.host_param_name: "1.1.1.1"}
        assert poller.get_driver(device) == poller.driver_factory.return_value
        poller.driver_factory.assert_called_once_with(**credentials, **{poller.host_param_name: "1.1.1.1"})

    def test_poll_one_command(self, get_mocked_poller):
        poller = get_mocked_poller({}, [], Mock())
        driver = Mock(**{"send_command.return_value": 1234})
        command = Mock(parameters={"cli_command": "show ver"})
        assert poller.poll_one_command(driver, command) == 1234
        driver.send_command.assert_called_once_with("show ver")

    @pytest.mark.parametrize("raise_exc", [True, False])
    def test_poll(self, get_mocked_poller, raise_exc, get_mocked_device):
        def poll(arg):
            time.sleep(0.1)
            if raise_exc:
                raise OSError
            return arg

        commands = [Mock(parameters={"cli_command": "a"}), Mock(parameters={"cli_command": "b"})]
        poller = get_mocked_poller({}, commands, Mock(**{"return_value.send_command": poll}))
        devices = [get_mocked_device(f"1.1.1.{i}") for i in range(10)]
        start = time.time()
        results = list(poller.poll(devices))
        assert time.time() - start < 1
        assert len(results) == len(commands) * len(devices)
        if raise_exc:
            assert all(res.error.message.startswith("OSError") for res in results)
        else:
            assert all(res.result in {"a", "b"} for res in results)


def test_http_driver():
    device = Mock(**{"primary_ip.address.ip": "1.1.1.1"})
    device.name = "d1"
    command = Mock(
        parameters={"url_path": "/some/path/", "method": "post", "body": {"a": "b", "device_name": "{{device.name}}"}}
    )
    creds = {
        "url": "https://{{device.primary_ip.address.ip}}{{command.parameters.url_path}}",
        "verify": True,
        "qwe": "rty",
    }
    driver = HttpDriver(device, **creds)
    requests = MagicMock()
    result = driver.request(command, requests=requests)
    requests.request.assert_called_once_with(
        url="https://1.1.1.1/some/path/",
        verify=True,
        qwe="rty",
        method="post",
        json={"a": "b", "device_name": "d1"},
        auth=None,
    )
    assert result == requests.request.return_value.content.decode.return_value


def test_poller_choices():
    poller_choices = PollerChoices(
        pollers_info=[
            PollerInfo(klass=NetmikoPoller, name="some_poller", color="red", command_types=["CLI"]),
            PollerInfo(
                klass=RequestsPoller, name="p2", verbose_name="P2", color="green", command_types=["json_api", "custom"]
            ),
        ]
    )
    assert poller_choices.choices == [("some_poller", "Some Poller"), ("p2", "P2")]
    assert poller_choices.colors == {"some_poller": "red", "p2": "green"}
    assert poller_choices.classes == {"some_poller": NetmikoPoller, "p2": RequestsPoller}
    assert poller_choices.command_types == {"some_poller": ["CLI"], "p2": ["json_api", "custom"]}
