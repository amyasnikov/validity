from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import ClassVar

import pygit2
from django.utils.translation import gettext as __
from extras.scripts import MultiObjectVar, Script

from validity import models, settings


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
    def from_db(cls, db_instance: models.GitRepo) -> "GitRepo":
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
        self._repo.head.set_target(remote_master_id)
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

    class Meta:
        name = __("Git Repositories Sync")
        description = __("Pull the updates for all or particular Git Repositories")

    @staticmethod
    def update_and_get_hash(db_repo: models.GitRepo) -> tuple[bool, str]:
        try:
            repo = GitRepo.from_db(db_repo)
            repo.clone_or_force_pull()
            return True, repo.head_hash
        except pygit2.GitError as e:
            return False, str(e)

    @staticmethod
    def format_script_output(hashes_map: dict) -> str:
        if not hashes_map:
            return ""
        col_size = max(len(max(hashes_map.keys(), key=len)), len("Repository")) + 2
        columns = chain([("Repository", "Hash"), ("", "")], hashes_map.items())
        return "\n".join(f"{repo:<{col_size}}{hash_}" for repo, hash_ in columns)

    def run(self, data, commit):
        all_db_repos = models.GitRepo.objects.order_by("id")
        if repo_ids := data.get("repos"):
            all_db_repos = all_db_repos.filter(id__in=repo_ids)
        with ThreadPoolExecutor() as tp:
            results = tp.map(self.update_and_get_hash, all_db_repos)
            successful_repo_ids = []
            new_repo_hashes = {}
            for repo, (is_success, msg) in zip(all_db_repos, results):
                if is_success:
                    repo.head_hash = msg
                    successful_repo_ids.append(repo.pk)
                    new_repo_hashes[repo.name] = msg
                else:
                    self.log_failure(f"{repo.name}: {msg}")
            models.GitRepo.objects.bulk_update(all_db_repos.filter(pk__in=successful_repo_ids), ["head_hash"])
            if successful_repo_ids:
                self.log_success(
                    f"Successfully updated {len(successful_repo_ids)} repositories. Check out the table below"
                )
            return self.format_script_output(new_repo_hashes)


name = "Git"
