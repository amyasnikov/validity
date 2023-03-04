from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

import pygit2
from django.conf import settings
from extras.scripts import Script

from validity import models


PLUGIN_CONFIG = settings.PLUGINS_CONFIG.get("validity", {})


@dataclass
class GitRepo:
    name: str
    remote_url: str
    branch: str
    _repo: pygit2.Repository | None = field(init=False)

    git_folder: ClassVar[Path] = Path(PLUGIN_CONFIG.get("GIT_FOLDER", "/etc/netbox/scripts"))

    def __post_init__(self):
        try:
            if self._repo is None:
                self._repo = pygit2.Repository(self.local_path)
        except pygit2.GitError:
            pass

    @classmethod
    def from_db(cls, db_instance: models.GitRepo) -> "GitRepo":
        return cls(name=db_instance.name, remote_url=db_instance.full_url, branch=db_instance.branch or 'master')

    @property
    def local_path(self) -> Path:
        return self.git_folder / self.name

    @property
    def exists(self) -> bool:
        return self._repo is not None

    def clone(self) -> None:
        assert not self.exists, f'Cannot clone into existing Repo: {self.name}'
        self._repo = pygit2.clone_repository(url=self.remote_url, path=self.local_path, checkout_branch=self.branch)

    def force_pull(self) -> None:
        assert self._repo is not None, f'Trying to pull into not existing repo {self.name}. Clone first'
        remote = self._repo.remotes['origin']
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

    def head_hash(self) -> 'str':
        assert self._repo is not None, f'Trying to get head from not existing repo {self.name}. Clone first'
        return str(self._repo.head.target)[:7]


class SyncGitRepos(Script):
    git_folder = Path(PLUGIN_CONFIG.get("GIT_FOLDER", "/etc/netbox/scripts"))

    def run(self, data, commit):
        repos = (GitRepo.from_db(db_repo) for db_repo in models.GitRepo.objects.iterator())
        
