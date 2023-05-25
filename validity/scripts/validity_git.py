from itertools import chain

from django.utils.translation import gettext as __
from extras.scripts import MultiObjectVar, Script

from validity import models
from validity.utils.git import SyncReposMixin


class SyncGitRepos(SyncReposMixin, Script):
    repos = MultiObjectVar(model=models.GitRepo, label=__("Repositories"), required=False)

    class Meta:
        name = __("Git Repositories Sync")
        description = __("Pull the updates for all or particular Git Repositories")

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
        new_repo_hashes = self.update_git_repos(all_db_repos)
        return self.format_script_output(new_repo_hashes)


name = "Validity Git"
