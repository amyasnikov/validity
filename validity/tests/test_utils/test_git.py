import os
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest
from factories import GitRepoFactory

from validity import models
from validity.utils.git import GitRepo, SyncReposMixin


@pytest.fixture
def set_git_folder(tests_root):
    GitRepo.git_folder = tests_root


@pytest.fixture
def create_repo_via_shell(tests_root):
    repo_paths = []

    def _create_repository(repo_name, origin=None):
        repo_path = tests_root / repo_name
        repo_paths.append(repo_path)
        init_content = "init_content"
        commands = (
            f"mkdir -p {repo_path}; cd {repo_path}; "
            f"git init; echo -n {init_content} > file.txt; "
            "git config user.name q; git config user.email 'q@q.q'; "
            "git add -A; git commit -m init; "
        )
        if origin:
            commands += f"git remote add origin {origin}"
        os.system(commands)
        return repo_path

    yield _create_repository
    for path in repo_paths:
        shutil.rmtree(path)


@pytest.fixture
def create_repo_via_gitrepo():
    repo_paths = []

    def _create_repository(repo_name, origin):
        repo = GitRepo(repo_name, origin, "master")
        repo_paths.append(repo.git_folder / repo.name)
        return repo

    yield _create_repository
    for path in repo_paths:
        shutil.rmtree(path)


@pytest.fixture
def make_commit(tests_root):
    def _make_commit(repo_name):
        repo_path = tests_root / repo_name
        os.system(f"cd {repo_path}; echo $RANDOM > file.txt; git add -A; git commit -m commit")
        return repo_path / ".git"

    return _make_commit


def file_content(repo_path: Path) -> str:
    with (repo_path / "file.txt").open("r") as file:
        return file.read()


def test_clone(create_repo_via_shell, set_git_folder, tests_root, create_repo_via_gitrepo):
    remote_repo_path = create_repo_via_shell("remote_repo")
    repo: GitRepo = create_repo_via_gitrepo("some_repo", f"file://{remote_repo_path}")
    repo.clone()
    assert (tests_root / "some_repo").is_dir()
    file_path = tests_root / "some_repo" / "file.txt"
    assert file_path.is_file()
    assert file_content(file_path.parent) == "init_content"


def test_force_pull(create_repo_via_shell, make_commit, set_git_folder):
    remote_repo_path = create_repo_via_shell("remote_repo")
    local_repo_path = create_repo_via_shell("local_repo", origin=remote_repo_path)
    make_commit("local_repo")
    local_repo = GitRepo("local_repo", f"file://{remote_repo_path}", "master")
    local_repo.force_pull()
    assert file_content(local_repo_path) == file_content(remote_repo_path)
    assert GitRepo("remote_repo", "", "master").head_hash == local_repo.head_hash


@pytest.mark.django_db
def test_update_git_repos(create_repo_via_shell, make_commit, set_git_folder, tests_root, monkeypatch):
    remote_repo_path = create_repo_via_shell("remote_repo")
    GitRepoFactory(name="local_repo", git_url=f"file://{remote_repo_path}")
    monkeypatch.setattr(SyncReposMixin, "log_success", Mock(), raising=False)
    sync_script = SyncReposMixin()
    sync_script.update_git_repos(models.GitRepo.objects.all())
    remote_repo = GitRepo("remote_repo", "", "master")
    local_repo = GitRepo("local_repo", "", "master")
    assert remote_repo.head_hash == local_repo.head_hash
    assert file_content(remote_repo_path) == file_content(tests_root / "local_repo")
