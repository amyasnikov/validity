import inspect
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, ClassVar

import pytest
from factories import BackupPointFactory, DataFileFactory

from validity.data_backup import BackupBackend, Backuper, GitBackuper, S3Backuper
from validity.data_backup.parameters import GitParams
from validity.integrations.data_models import GitFileChange, GitStatus
from validity.integrations.git import GitClient
from validity.integrations.s3 import S3Client
from validity.utils.logger import Logger


@dataclass
class TestBackuper(Backuper):
    test_func: Callable
    parameters_cls: ClassVar[type] = GitParams

    def _do_backup(self, url, parameters, datasource_dir):
        self.test_func(url, parameters, datasource_dir)


def backup_backend(test_func):
    backuper = TestBackuper(Logger(), test_func)
    return BackupBackend({"git": backuper})


@dataclass
class MockClient:
    operations: list[tuple[str, dict]] = field(default_factory=list, init=False)

    def _args(self, method_name, args, kwargs):
        method = getattr(super(), method_name)
        return inspect.signature(method).bind(*args, **kwargs).arguments

    def _addop(self, op, args):
        self.operations.append((op, args))


@dataclass
class MockGitClient(MockClient, GitClient):
    _status: GitStatus
    operations: list[tuple[str, dict]] = field(default_factory=list, init=False)

    def clone(self, *args, **kwargs):
        self._addop("clone", self._args("clone", args, kwargs))

    def stage_all(self, local_path):
        self._addop("stage_all", {"local_path": local_path})

    def unstage_all(self, local_path):
        self._addop("unstage_all", {"local_path": local_path})

    def commit(self, *args, **kwargs):
        self._addop("commit", self._args("commit", args, kwargs))

    def push(self, *args, **kwargs):
        self._addop("push", self._args("push", args, kwargs))

    def status(self, local_path):
        return self._status


class MockS3Client(MockClient, S3Client):
    def upload_file(self, path, url, access_key_id, secret_access_key):
        assert path.is_file()
        assert str(path).endswith("a.zip")
        self._addop(
            "upload_file",
            {"path": path, "url": url, "access_key_id": access_key_id, "secret_access_key": secret_access_key},
        )

    def upload_folder(self, *args, **kwargs):
        self._addop("upload_folder", self._args("upload_folder", args, kwargs))


@pytest.mark.django_db
def test_backup_backend():
    def test_backend(url, parameters, datasource_dir):
        assert url == bp.url
        assert parameters.username == bp.parameters.decrypted["username"]
        assert parameters.password == bp.parameters.decrypted["password"]
        f1 = datasource_dir / "f1.txt"
        f2 = datasource_dir / "folder" / "f2.txt"
        assert f1.is_file()
        assert f2.is_file()

    backend = backup_backend(test_backend)
    bp = BackupPointFactory(method="git")
    DataFileFactory(path="f1.txt", source=bp.data_source)
    DataFileFactory(path="folder/f2.txt", source=bp.data_source)
    backend(bp)


def test_git_backuper_with_changes():
    client = MockGitClient(
        _status=GitStatus(staged=GitFileChange(add=[], delete=[], modify=[]), unstaged=["somefile"], untracked=[])
    )

    backuper = GitBackuper(Logger(), message="msg", author_username="ada", author_email="ada@e.com", git_client=client)
    backuper("http://e.com/a", {"username": "a", "password": "b"}, Path("/tmp"))
    assert client.operations == [
        (
            "clone",
            {
                "local_path": "/tmp",
                "remote_url": "http://e.com/a",
                "branch": None,
                "username": "a",
                "password": "b",
                "depth": 1,
                "checkout": False,
            },
        ),
        ("unstage_all", {"local_path": "/tmp"}),
        ("stage_all", {"local_path": "/tmp"}),
        ("commit", {"local_path": "/tmp", "username": "ada", "email": "ada@e.com", "message": "msg"}),
        (
            "push",
            {"local_path": "/tmp", "remote_url": "http://e.com/a", "branch": None, "username": "a", "password": "b"},
        ),
    ]


def test_git_backuper_no_changes():
    client = MockGitClient(
        _status=GitStatus(staged=GitFileChange(add=[], delete=[], modify=[]), unstaged=[], untracked=[])
    )
    backuper = GitBackuper(Logger(), message="msg", author_username="ada", author_email="ada@e.com", git_client=client)
    backuper("http://e.com/a", {"username": "a", "password": "b", "branch": "main"}, Path("/tmp"))
    assert client.operations == [
        (
            "clone",
            {
                "local_path": "/tmp",
                "remote_url": "http://e.com/a",
                "branch": "main",
                "username": "a",
                "password": "b",
                "depth": 1,
                "checkout": False,
            },
        ),
        ("unstage_all", {"local_path": "/tmp"}),
    ]


def test_s3_backuper_noarchive():
    client = MockS3Client()
    backuper = S3Backuper(Logger(), client)
    backuper(
        "http://s3.com/buck/fold",
        {"aws_access_key_id": "123", "aws_secret_access_key": "456", "archive": False},
        Path("/tmp"),
    )
    assert client.operations == [
        (
            "upload_folder",
            {
                "path": Path("/tmp"),
                "url": "http://s3.com/buck/fold",
                "access_key_id": "123",
                "secret_access_key": "456",
            },
        )
    ]


def test_s3_backuper_archive():
    client = MockS3Client()
    backuper = S3Backuper(Logger(), client)
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        f1 = tmpdir / "f1.txt"
        f2 = tmpdir / "f2.txt"
        f1.write_text("f1_contents")
        f2.write_text("f2_contents")
        backuper(
            "http://s3.com/buck/arch.zip",
            {"aws_access_key_id": "123", "aws_secret_access_key": "456", "archive": True},
            tmpdir,
        )
        assert str(client.operations[0][1]["path"]).endswith("a.zip")
        client.operations[0][1]["path"] = ""  # path is alway different and cannot be compared
        assert client.operations == [
            (
                "upload_file",
                {"path": "", "url": "http://s3.com/buck/arch.zip", "access_key_id": "123", "secret_access_key": "456"},
            )
        ]
