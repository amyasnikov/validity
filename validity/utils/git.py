from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pygit2
from django.db.models import QuerySet

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


class SyncReposMixin:
    """
    Mixin for scripts to sync Git Repositories
    """

    @staticmethod
    def update_and_get_hash(db_repo: "models.GitRepo") -> tuple[bool, str]:
        try:
            repo = GitRepo.from_db(db_repo)
            repo.clone_or_force_pull()
            return True, repo.head_hash
        except pygit2.GitError as e:
            return False, str(e)

    def update_git_repos(self, db_repos: QuerySet["models.GitRepo"]) -> dict[str, str]:
        with ThreadPoolExecutor() as tp:
            results = tp.map(self.update_and_get_hash, db_repos)
            successful_repo_ids = []
            new_repo_hashes = {}
            for repo, (is_success, msg) in zip(db_repos, results):
                if is_success:
                    repo.head_hash = msg
                    successful_repo_ids.append(repo.pk)
                    new_repo_hashes[repo.name] = msg
                else:
                    self.log_failure(f"{repo.name}: {msg}")
            db_repos.model.objects.bulk_update(db_repos.filter(pk__in=successful_repo_ids), ["head_hash"])
            if successful_repo_ids:
                self.log_success(f"Successfully updated {len(successful_repo_ids)} repositories")
            return new_repo_hashes
