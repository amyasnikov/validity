from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from django.utils.text import slugify

from .exceptions import PollingError


if TYPE_CHECKING:
    from validity.models import Command, VDevice


@dataclass(frozen=True)
class DescriptiveError:
    """
    This info will be added to polling_info.yaml
    """

    device: str
    command: str | None
    error: str

    @property
    def serialized(self):
        result = {"device": self.device, "error": self.error}
        if self.command:
            result["command"] = self.command
        return result


@dataclass
class CommandResult:
    device: "VDevice"
    command: "Command"
    result: str = ""
    error: PollingError | None = None

    error_header: ClassVar[str] = "POLLING ERROR\n"

    def __post_init__(self):
        assert self.result or self.error is not None

    foldername = property(lambda self: slugify(str(self.device)))
    filename = property(lambda self: self.command.label + ".txt")
    errored = property(lambda self: self.error is not None)
    contents = property(lambda self: self.error_header + str(self.error) if self.errored else self.result)

    @property
    def descriptive_error(self):
        assert self.errored
        command = "" if self.error.device_wide else self.command.label
        return DescriptiveError(device=str(self.device), command=command, error=self.error.message)

    def write_on_disk(self, base_dir: str) -> None:
        device_folder = Path(base_dir) / self.foldername
        if not device_folder.is_dir():
            device_folder.mkdir()
        full_path = device_folder / self.filename
        full_path.write_text(self.contents, encoding="utf-8")
