from abc import ABC, abstractmethod
from itertools import chain

from dulwich import porcelain
from dulwich.ignore import IgnoreFilterManager
from dulwich.index import get_unstaged_changes
from dulwich.repo import Repo


class GitClient(ABC):
    @abstractmethod
    def clone(
        self, local_path: str, remote_url: str, branch: str = "", username: str = "", password: str = "", depth: int = 0
    ) -> None: ...

    @abstractmethod
    def stage_all(self, repo_path: str) -> None: ...

    @abstractmethod
    def commit(self, repo_path: str, username: str, email: str, message: str) -> str:
        """
        Returns SHA1 hash of the new commit
        """

    @abstractmethod
    def push(
        self, local_path: str, remote_url: str, branch: str, username: str, password: str, force: bool = False
    ) -> None: ...


class DulwichGitClient(GitClient):
    def clone(
        self, local_path: str, remote_url: str, branch: str = "", username: str = "", password: str = "", depth: int = 0
    ) -> None:
        optional_args = {}
        if branch:
            optional_args["branch"] = branch
        if username:
            optional_args["username"] = username
        if password:
            optional_args["password"] = password
        optional_args["depth"] = depth or None
        porcelain.clone(remote_url, local_path, **optional_args)

    def stage_all(self, repo_path: str) -> None:
        repo = Repo(repo_path)
        ignore_mgr = IgnoreFilterManager.from_repo(repo)
        unstaged_files = (fn.decode("utf-8") for fn in get_unstaged_changes(repo.open_index(), repo_path))
        untracked_files = porcelain.get_untracked_paths(repo_path, repo_path, repo.open_index())
        files = (file for file in chain(unstaged_files, untracked_files) if not ignore_mgr.is_ignored(file))
        repo.stage(files)

    def commit(self, repo_path: str, username: str, email: str, message: str) -> str:
        author = f"{username} <{email}>".encode("utf-8")
        commit_hash = porcelain.commit(repo=repo_path, author=author, committer=author, message=message.encode("utf-8"))
        return commit_hash.decode("utf-8")

    def push(
        self, local_path: str, remote_url: str, branch: str, username: str, password: str, force: bool = False
    ) -> None:
        porcelain.push(
            local_path, remote_url, refspecs=branch.encode("utf-8"), force=force, username=username, password=password
        )
