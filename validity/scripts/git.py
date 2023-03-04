from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

import pygit2
from django.utils.translation import gettext_lazy as __
from extras.scripts import MultiObjectVar, Script

from validity import models, settings


@dataclass
class GitRepo:
    name: str
    remote_url: str
    branch: str
    _repo: pygit2.Repository | None = field(init=False)

    git_folder: ClassVar[Path] = settings.git_folder

    def __post_init__(self):
        try:
            if self._repo is None:
                self._repo = pygit2.Repository(self.local_path)
        except pygit2.GitError:
            pass

    @classmethod
    def from_db(cls, db_instance: models.GitRepo) -> "GitRepo":
        return cls(name=db_instance.name, remote_url=db_instance.full_url, branch=db_instance.branch or "master")

    @property
    def local_path(self) -> Path:
        return self.git_folder / self.name

    @property
    def exists(self) -> bool:
        return self._repo is not None

    def clone(self) -> None:
        assert not self.exists, f"Cannot clone into existing Repo: {self.name}"
        self._repo = pygit2.clone_repository(url=self.remote_url, path=self.local_path, checkout_branch=self.branch)

    def force_pull(self) -> None:
        assert self._repo is not None, f"Trying to pull into not existing repo {self.name}. Clone first"
        remote = self._repo.remotes["origin"]
        remote.fetch()
        remote_master_id = self._repo.lookup_reference(f"refs/remotes/origin/{self.branch}").target
        repo_branch = self._repo.lookup_reference("refs/heads/%s" % self.branch)
        repo_branch.set_target(remote_master_id)
        merge_result, _ = self._repo.merge_analysis(remote_master_id)
        # Up to date, do nothing
        if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            return
        # We can just fastforward
        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
            self._repo.checkout_tree(self._repo.get(remote_master_id))
            master_ref = self._repo.lookup_reference("refs/heads/{self.branch}")
            master_ref.set_target(remote_master_id)
            self._repo.head.set_target(remote_master_id)
        else:
            raise AssertionError(f"Unknown merge analysis result for {self.name}")

    def clone_or_force_pull(self) -> None:
        if self.exists:
            self.force_pull()
        else:
            self.clone()

    @property
    def head_hash(self) -> "str":
        assert self._repo is not None, f"Trying to get head from not existing repo {self.name}. Clone first"
        return str(self._repo.head.target)[:7]


class SyncGitRepos(Script):
    repos = MultiObjectVar(model=models.GitRepo, label=__("Repositories"), required=False)

    @staticmethod
    def update_and_get_hash(db_repo: models.GitRepo) -> str:
        repo = GitRepo.from_db(db_repo)
        repo.clone_or_force_pull()
        return repo.head_hash

    def run(self, data, commit):
        all_db_repos = models.GitRepo.objects.order_by("id")
        if repo_ids := data.get("repos"):
            all_db_repos = all_db_repos.filter(id__in=repo_ids)
        with ThreadPoolExecutor() as tp:
            head_hashes = tp.map(self.update_and_get_hash, all_db_repos)
            for repo, hash in zip(all_db_repos, head_hashes):
                repo.head_hash = hash
