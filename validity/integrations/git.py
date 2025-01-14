from abc import ABC, abstractmethod
from itertools import chain

from dulwich import porcelain
from dulwich.ignore import IgnoreFilterManager
from dulwich.index import get_unstaged_changes
from dulwich.repo import Repo

from validity.utils.misc import reraise
from .data_models import GitStatus
from .errors import IntegrationError


class GitClient(ABC):
    @abstractmethod
    def clone(
        self,
        local_path: str,
        remote_url: str,
        branch: str = "",
        username: str = "",
        password: str = "",
        depth: int = 0,
        checkout: bool = True,
    ) -> None: ...

    @abstractmethod
    def stage_all(self, local_path: str) -> None: ...

    @abstractmethod
    def unstage_all(self, local_path: str) -> None: ...

    @abstractmethod
    def commit(self, local_path: str, username: str, email: str, message: str) -> str:
        """
        Returns SHA1 hash of the new commit
        """

    @abstractmethod
    def push(
        self, local_path: str, remote_url: str, branch: str, username: str, password: str, force: bool = False
    ) -> None: ...

    @abstractmethod
    def status(self, local_path: str) -> GitStatus: ...


class DulwichGitClient(GitClient):
    def clone(
        self,
        local_path: str,
        remote_url: str,
        branch: str = "",
        username: str = "",
        password: str = "",
        depth: int = 0,
        checkout: bool = True,
    ) -> None:
        optional_args = {}
        if branch:
            optional_args["branch"] = branch
        if username:
            optional_args["username"] = username
        if password:
            optional_args["password"] = password
        optional_args["depth"] = depth or None
        with reraise(Exception, IntegrationError):
            porcelain.clone(remote_url, local_path, checkout=checkout, **optional_args)

    def stage_all(self, local_path: str) -> None:
        repo = Repo(local_path)
        ignore_mgr = IgnoreFilterManager.from_repo(repo)
        unstaged_files = (fn.decode() for fn in get_unstaged_changes(repo.open_index(), local_path))
        untracked_files = porcelain.get_untracked_paths(local_path, local_path, repo.open_index())
        files = (file for file in chain(unstaged_files, untracked_files) if not ignore_mgr.is_ignored(file))
        repo.stage(files)

    def unstage_all(self, local_path: str) -> None:
        repo = Repo(local_path)
        staged_files = chain.from_iterable(porcelain.status(local_path).staged.values())
        repo.unstage(filename.decode() for filename in staged_files)

    def commit(self, local_path: str, username: str, email: str, message: str) -> str:
        author = f"{username} <{email}>".encode()
        commit_hash = porcelain.commit(repo=local_path, author=author, committer=author, message=message.encode())
        return commit_hash.decode()

    def push(
        self, local_path: str, remote_url: str, branch: str, username: str, password: str, force: bool = False
    ) -> None:
        branch = branch.encode() if branch else porcelain.active_branch(local_path)
        with reraise(Exception, IntegrationError):
            porcelain.push(local_path, remote_url, refspecs=branch, force=force, username=username, password=password)

    def status(self, local_path: str) -> GitStatus:
        status = porcelain.status(local_path)
        return GitStatus.model_validate(status)
