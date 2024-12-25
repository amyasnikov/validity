import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, ClassVar

from pydantic import BaseModel

from validity.integrations.git import GitClient
from validity.integrations.s3 import S3Client
from validity.utils.filesystem import merge_directories
from .entities import RemoteGitRepo
from .parameters import GitParams, S3Params


class Backuper(ABC):
    parameters_cls: type[BaseModel]

    def __call__(self, url: str, parameters: dict[str, Any], datasource_dir: Path) -> None:
        validated_params = self.parameters_cls.model_validate(parameters)
        self._do_backup(url, validated_params, datasource_dir)

    @abstractmethod
    def _do_backup(self, url: str, parameters: BaseModel, datasource_dir: Path) -> None: ...


@dataclass
class GitBackuper(Backuper):
    message: str
    author_username: str
    author_email: str
    git_client: GitClient

    parameters_cls: ClassVar[type[BaseModel]] = GitParams

    def _do_backup(self, url: str, parameters: GitParams, datasource_dir: Path) -> None:
        with TemporaryDirectory() as repo_dir:
            repo = RemoteGitRepo(
                local_path=repo_dir,
                remote_url=url,
                active_branch=parameters.branch,
                username=parameters.username,
                password=parameters.password,
                client=self.git_client,
            )
            repo.download()
            merge_directories(datasource_dir, repo.local_path)
            repo.save_changes(self.author_username, self.author_email, message=self.message)
            repo.upload()


@dataclass
class S3Backuper(Backuper):
    s3_client: S3Client

    parameters_cls: ClassVar[type[BaseModel]] = S3Params

    def _backup_archive(self, url: str, parameters: S3Params, datasource_dir: Path) -> None:
        with TemporaryDirectory() as backup_dir:
            archive = Path(backup_dir) / "a.zip"
            shutil.make_archive(archive, "zip", datasource_dir)
            self.s3_client.upload_file(archive, url, parameters.aws_access_key_id, parameters.aws_secret_access_key)

    def _backup_dir(self, url: str, parameters: S3Params, datasource_dir: Path) -> None:
        self.s3_client.upload_folder(
            datasource_dir, url, parameters.aws_access_key_id, parameters.aws_secret_access_key
        )

    def _do_backup(self, url: str, parameters: S3Params, datasource_dir: Path):
        if parameters.archive:
            self._backup_archive(url, parameters, datasource_dir)
        else:
            self._backup_dir(url, parameters, datasource_dir)
