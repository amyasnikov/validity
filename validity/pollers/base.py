from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, Collection, Iterable, Iterator

from validity.utils.misc import reraise
from .exceptions import PollingError
from .result import CommandResult


if TYPE_CHECKING:
    from validity.models import Command, VDevice


class DevicePoller(ABC):
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


class ThreadPoller(DevicePoller):
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
    driver_cls: type  # Network driver class, e.g. netmiko.ConnectHandler

    def get_driver(self, device: "VDevice"):
        creds = self.get_credentials(device)
        return self.driver_cls(**creds)


class ConsecutivePoller(DriverMixin, ThreadPoller):
    @abstractmethod
    def poll_one_command(self, driver: Any, command: "Command") -> str:
        pass

    def poll_one_device(self, device: "VDevice") -> Iterator[CommandResult]:
        driver = self.get_driver(device)
        for command in self.commands:
            try:
                with reraise(Exception, PollingError, device_wide=False):
                    output = self.poll_one_command(driver, command)
                    yield CommandResult(device=device, command=command, result=output)
            except PollingError as err:
                yield CommandResult(device=device, command=command, error=err)
