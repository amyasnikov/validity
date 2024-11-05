from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Collection, Iterable, Iterator

from validity.utils.misc import reraise
from .exceptions import PollingError
from .result import CommandResult


if TYPE_CHECKING:
    from validity.models import Command, VDevice


class BasePoller(ABC):
    host_param_name: str

    def __init__(self, credentials: dict, commands: Collection["Command"]) -> None:
        self.credentials = credentials
        self.commands = commands

    @abstractmethod
    def poll(self, devices: Iterable["VDevice"]) -> Iterator[CommandResult]:
        pass

    def get_credentials(self, device: "VDevice"):
        if (ip := device.primary_ip) is None:
            raise PollingError(message="Device has no primary IP")
        return self.credentials | {self.host_param_name: str(ip.address.ip)}


class ThreadPoller(BasePoller):
    """
    Polls devices one by one using threads
    """

    def __init__(self, credentials: dict, commands: Collection["Command"], thread_workers: int = 500) -> None:
        super().__init__(credentials, commands)
        self.thread_workers = thread_workers

    def _poll_one_device(self, device: "VDevice") -> Collection[CommandResult]:
        """
        Handles device-wide errors
        """
        try:
            with reraise(Exception, PollingError):
                return list(self.poll_one_device(device))
        except PollingError as err:
            return [CommandResult(device, c, error=err) for c in self.commands]

    @abstractmethod
    def poll_one_device(self, device: "VDevice") -> Iterator[CommandResult]:
        pass

    def _poll(self, devices: Iterable["VDevice"]) -> Iterator[CommandResult]:
        with ThreadPoolExecutor(max_workers=self.thread_workers) as executor:
            results = [executor.submit(self._poll_one_device, d) for d in devices]
            yield  # start threadpool and release the generator
            for result in as_completed(results):
                yield from result.result()

    def poll(self, devices: Iterable["VDevice"]) -> Iterator[CommandResult | PollingError]:
        poll_gen = self._poll(devices)
        next(poll_gen)
        return poll_gen


class DriverMixin:
    driver_factory: Callable  # Network driver class, e.g. netmiko.ConnectHandler
    driver_connect_method: str = ""
    driver_disconnect_method: str = ""

    def connect(self, credentials: dict[str, Any]):
        driver = type(self).driver_factory(**credentials)
        if self.driver_connect_method:
            getattr(driver, self.driver_connect_method)()
        return driver

    def disconnect(self, driver):
        if self.driver_disconnect_method:
            getattr(driver, self.driver_disconnect_method)()

    @contextmanager
    def connection(self, device: "VDevice"):
        creds = self.get_credentials(device)
        driver = self.connect(creds)
        try:
            yield driver
        finally:
            self.disconnect(driver)


class ConsecutivePoller(DriverMixin, ThreadPoller):
    @abstractmethod
    def poll_one_command(self, driver: Any, command: "Command") -> str:
        pass

    def poll_one_device(self, device: "VDevice") -> Iterator[CommandResult]:
        with self.connection(device) as driver:
            for command in self.commands:
                try:
                    with reraise(Exception, PollingError, device_wide=False):
                        output = self.poll_one_command(driver, command)
                        yield CommandResult(device=device, command=command, result=output)
                except PollingError as err:
                    yield CommandResult(device=device, command=command, error=err)


class CustomPoller(ConsecutivePoller):
    """
    Base class for creating user-defined pollers
    To define your own poller override the following attributes:
    - driver_factory - class/function for creating connection to particular device
    - host_param_name - name of the driver parameter which holds device IP address
    - poll_one_command() - method for sending one particular command to device and retrieving the result
    - driver_connect_method - optional driver method name to initiate the connection
    - driver_disconnect_method - optional driver method name to gracefully terminate the connection
    """
