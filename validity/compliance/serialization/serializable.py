from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Optional

from core.models import DataFile

from ..exceptions import BadDataFileContentsError, NoComponentError


if TYPE_CHECKING:
    from validity.models import Serializer


@dataclass(frozen=True)
class Serializable:
    serializer: Optional["Serializer"]
    data_file: DataFile | None

    @cached_property
    def serialized(self):
        if self.data_file is None:
            raise NoComponentError("Data File")
        if self.serializer is None:
            raise NoComponentError("Serializer")
        if (file_data := self.data_file.data_as_string) is not None:
            return self.serializer.serialize(file_data)
        raise BadDataFileContentsError(f"Cannot decode data file {self.data_file.path}")
