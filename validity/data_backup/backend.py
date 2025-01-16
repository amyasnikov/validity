from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from validity.models import BackupPoint
    from .backupers import Backuper


class BackupBackend:
    def __init__(self, backupers: dict[str, "Backuper"]):
        self.backupers = backupers

    @contextmanager
    def _datasource_in_filesytem(self, backup_point: "BackupPoint"):
        with TemporaryDirectory() as datasource_dir:
            datasource_dir = Path(datasource_dir)
            for file in backup_point.data_source.datafiles.all():
                if not backup_point.ignore_file(file.path):
                    filepath = datasource_dir / file.path
                    filepath.parent.mkdir(exist_ok=True, parents=True)
                    file.write_to_disk(datasource_dir / file.path)
            yield datasource_dir

    def __call__(self, backup_point: "BackupPoint") -> None:
        backuper = self.backupers[backup_point.method]
        with self._datasource_in_filesytem(backup_point) as datasource_dir:
            backuper(backup_point.url, backup_point.parameters.decrypted, datasource_dir)
