from dataclasses import dataclass

from validity.integrations.git import GitClient


@dataclass(slots=True, kw_only=True)
class RemoteGitRepo:
    local_path: str
    remote_url: str
    active_branch: str
    username: str = ""
    password: str = ""
    client: GitClient

    def save_changes(self, author_username: str, author_email: str, message: str = "") -> None:
        self.client.stage_all(self.local_path)
        self.client.commit(self.local_path, author_username, author_email, message)

    def download(self, dotgit_only: bool = False) -> None:
        self.client.clone(
            self.local_path,
            self.remote_url,
            self.active_branch,
            self.username,
            self.password,
            depth=1,
            checkout=not dotgit_only,
        )
        if dotgit_only:
            self.client.unstage_all(self.local_path)

    def upload(self) -> None:
        self.client.push(self.local_path, self.remote_url, self.active_branch, self.username, self.password)

    @property
    def has_changes(self) -> bool:
        return self.client.status(self.local_path).has_changes
