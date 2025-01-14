import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, ClassVar

from pydantic import BaseModel

from validity.integrations.git import GitClient
from validity.integrations.s3 import S3Client
from validity.utils.logger import Logger
from .entities import RemoteGitRepo
from .parameters import GitParams, S3Params


@dataclass
class Backuper(ABC):
    logger: Logger

    parameters_cls: ClassVar[type[BaseModel]]

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

    def _get_repo(self, url: str, parameters: GitParams, datasource_dir: Path) -> RemoteGitRepo:
        return RemoteGitRepo(
            local_path=str(datasource_dir),
            remote_url=url,
            active_branch=parameters.branch,
            username=parameters.username,
            password=parameters.password,
            client=self.git_client,
        )

    def _do_backup(self, url: str, parameters: GitParams, datasource_dir: Path) -> None:
        repo = self._get_repo(url, parameters, datasource_dir)
        repo.download(dotgit_only=True)
        if repo.has_changes:
            repo.save_changes(self.author_username, self.author_email, message=self.message)
            repo.upload()
            self.logger.info(f"Data successfully git-pushed to `{url}`")
        else:
            self.logger.info(f"No diff found for `{url}`, skipping git push")


@dataclass
class S3Backuper(Backuper):
    s3_client: S3Client

    parameters_cls: ClassVar[type[BaseModel]] = S3Params

    def _backup_archive(self, url: str, parameters: S3Params, datasource_dir: Path) -> None:
        with TemporaryDirectory() as backup_dir:
            archive = Path(backup_dir) / "a.zip"
            shutil.make_archive(archive.with_suffix(""), "zip", datasource_dir)
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
        self.logger.info(f"Data uploaded to S3 storage: `{url}`")
