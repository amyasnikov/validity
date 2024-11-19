from typing import TYPE_CHECKING

from scrapli_netconf.driver import NetconfDriver

from .base import ConsecutivePoller


if TYPE_CHECKING:
    from validity.models import Command


class ScrapliNetconfPoller(ConsecutivePoller):
    driver_factory = NetconfDriver
    driver_connect_method = "open"
    driver_disconnect_method = "close"
    host_param_name = "host"

    def poll_one_command(self, driver: NetconfDriver, command: "Command") -> str:
        response = driver.rpc(command.parameters["rpc"])
        return response.result
