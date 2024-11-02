from typing import TYPE_CHECKING

from netmiko import BaseConnection, ConnectHandler

from .base import ConsecutivePoller


if TYPE_CHECKING:
    from validity.models import Command


class NetmikoPoller(ConsecutivePoller):
    host_param_name = "host"
    driver_disconnect_method = "disconnect"
    driver_factory = ConnectHandler

    def poll_one_command(self, driver: BaseConnection, command: "Command") -> str:
        return driver.send_command(command.parameters["cli_command"])
