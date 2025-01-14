from unittest.mock import Mock

import pytest
from django.utils import timezone

from validity.choices import BackupStatusChoices
from validity.data_backup import BackupBackend
from validity.models import BackupPoint


def test_dobackup_success(di):
    backend = Mock()
    start = timezone.now()
    with di.override({BackupBackend: lambda: backend}):
        bp = BackupPoint(name="bp")
        bp.do_backup()
        backend.assert_called_once_with(bp)
        assert bp.last_uploaded > start
        assert bp.last_status == BackupStatusChoices.completed
        assert bp.last_error == ""


def test_dobackup_fail(di):
    backend = Mock(side_effect=ValueError("QWERTY"))
    start = timezone.now()
    with di.override({BackupBackend: lambda: backend}):
        bp = BackupPoint(name="bp")
        with pytest.raises(ValueError):
            bp.do_backup()
        backend.assert_called_once_with(bp)
        assert bp.last_uploaded > start
        assert bp.last_status == BackupStatusChoices.failed
        assert bp.last_error == "ValueError('QWERTY')"


def test_ignore_file():
    bp = BackupPoint(ignore_rules="*.txt\nfolder1/*")
    ignore = ["1.txt", "fol/fi.txt", "folder1/Dockerfile"]
    noignore = ["1.doc", "folder2/Dockerfile"]

    for file in ignore:
        assert bp.ignore_file(file)

    for file in noignore:
        assert not bp.ignore_file(file)
