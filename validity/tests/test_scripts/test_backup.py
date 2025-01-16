import uuid
from unittest.mock import Mock

import pytest
from django.utils import timezone
from factories import DSBackupJobFactory

from validity.data_backup import BackupBackend
from validity.integrations.errors import IntegrationError
from validity.scripts.backup import perform_backup
from validity.scripts.data_models import FullBackUpParams


@pytest.fixture
def params(db):
    job = DSBackupJobFactory()
    return FullBackUpParams(
        request={"id": uuid.uuid4(), "user_id": 10},
        backuppoint_id=job.object.pk,
        job_id=job.pk,
        object_id=job.object.pk,
    )


@pytest.mark.django_db
def test_backup_success(di, params):
    job = params.get_job()
    backend = Mock()
    with di.override({BackupBackend: lambda: backend}):
        perform_backup(params)
    backend.assert_called_once_with(job.object)
    job.refresh_from_db()
    bp = job.object
    assert bp.last_status == "completed"
    assert bp.last_uploaded < timezone.now()
    assert job.status == "completed"
    assert job.data["log"]


@pytest.mark.django_db
def test_backup_failure(di, params):
    job = params.get_job()
    backend = Mock(side_effect=IntegrationError("ERROR!!!"))
    with di.override({BackupBackend: lambda: backend}):
        perform_backup(params)
    backend.assert_called_once_with(job.object)
    job.refresh_from_db()
    bp = job.object
    assert bp.last_status == "failed"
    assert bp.last_uploaded < timezone.now()
    assert bp.last_error == "IntegrationError('ERROR!!!')"
    assert job.status == "failed"
