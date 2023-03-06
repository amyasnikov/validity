from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pygit2

from validity import settings


if TYPE_CHECKING:
    from validity import models


@dataclass
class GitRepo:
    name: str
    remote_url: str
    branch: str
    _repo: pygit2.Repository | None = field(init=False, default=None, repr=False)

    git_folder: ClassVar[Path] = settings.git_folder

    def __post_init__(self):
        try:
            if self._repo is None:
                self._repo = pygit2.Repository(self.local_path)
        except pygit2.GitError:
            pass

    @classmethod
    def from_db(cls, db_instance: "models.GitRepo") -> "GitRepo":
        return cls(name=db_instance.name, remote_url=db_instance.full_git_url, branch=db_instance.branch)

    @property
    def local_path(self) -> Path:
        return self.git_folder / self.name

    @property
    def exists(self) -> bool:
        return self._repo is not None

    def clone(self) -> None:
        assert not self.exists, f"Cannot clone into existing Repo: {self.name}"
        try:
            self._repo = pygit2.clone_repository(url=self.remote_url, path=self.local_path, checkout_branch=self.branch)
        except KeyError as e:
            raise pygit2.GitError(str(e)) from e

    def force_pull(self) -> None:
        assert self._repo is not None, f"Trying to pull into not existing repo {self.name}. Clone first"
        remote = self._repo.remotes["origin"]
        remote.fetch()
        try:
            remote_master_id = self._repo.lookup_reference(f"refs/remotes/origin/{self.branch}").target
        except KeyError as e:
            raise pygit2.GitError(f"Unknown branch: {e}") from e
        self._repo.reset(remote_master_id, pygit2.GIT_RESET_HARD)

    def clone_or_force_pull(self) -> None:
        if self.exists:
            self.force_pull()
        else:
            self.clone()

    @property
    def head_hash(self) -> "str":
        assert self._repo is not None, f"Trying to get head from not existing repo {self.name}. Clone first"
        return str(self._repo.head.target)[:7]
