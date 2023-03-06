from concurrent.futures import ThreadPoolExecutor
from itertools import chain

import pygit2
from django.utils.translation import gettext as __
from extras.scripts import MultiObjectVar, Script

from validity import models
from validity.config_compliance.git import GitRepo


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


name = "Validity Git"
