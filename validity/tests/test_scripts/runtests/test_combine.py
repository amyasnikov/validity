import datetime
from dataclasses import replace
from unittest.mock import Mock

import pytest
from django.utils import timezone

from validity.scripts.data_models import ExecutionResult, Message
from validity.scripts.data_models import TestResultRatio as ResultRatio
from validity.scripts.exceptions import AbortScript
from validity.scripts.runtests.combine import CombineWorker


@pytest.fixture
def worker():
    return CombineWorker(
        testresult_queryset=Mock(), job_extractor_factory=Mock(), enqueue_func=Mock(), report_queryset=Mock()
    )


@pytest.fixture
def messages():
    time = datetime.datetime(2000, 1, 1)
    return [Message(status="info", message=f"m-{i}", time=time) for i in range(5)]


@pytest.fixture
def job_extractor(messages):
    extractor = Mock()
    extractor.parents = [Mock(), Mock()]
    extractor.parent.parent.job.result.log = messages[:1]
    extractor.parents[0].job.result = ExecutionResult(test_stat=ResultRatio(2, 2), log=messages[1:3])
    extractor.parents[1].job.result = ExecutionResult(test_stat=ResultRatio(1, 5), log=messages[3:])
    return extractor


# the test itself does not require db access,
# but according to netbox4.0 strange behaviour reverse() finally causes it
@pytest.mark.django_db
def test_compose_logs(worker, messages, job_extractor):
    logger = worker.log_factory()
    time = messages[0].time
    logs = worker.compose_logs(logger, job_extractor, report_id=10)
    assert len(logs) == 6
    assert logs[:5] == messages
    last_msg = replace(logs[-1], time=time)
    assert last_msg == Message(
        status="success",
        message="Job succeeded. See [Compliance Report](/plugins/validity/reports/10/) for detailed statistics",
        time=time,
    )


@pytest.mark.django_db
def test_call_abort(worker, full_runtests_params, job_extractor, monkeypatch):
    job_extractor.parents[1].job.result.errored = True
    monkeypatch.setattr(timezone, "now", lambda: datetime.datetime(2020, 1, 1))
    worker.job_extractor_factory = lambda: job_extractor
    with pytest.raises(AbortScript):
        worker(full_runtests_params)
    job = full_runtests_params.get_job()
    assert job.status == "errored"
    assert job.data == {
        "log": [
            {"message": "m-3", "status": "info", "time": "2000-01-01T00:00:00"},
            {"message": "m-4", "status": "info", "time": "2000-01-01T00:00:00"},
            {"message": "ApplyWorkerError", "status": "failure", "time": "2020-01-01T00:00:00"},
            {"message": "Database changes have been reverted", "status": "info", "time": "2020-01-01T00:00:00"},
        ],
        "output": None,
    }
    assert job.error == "AbortScript('ApplyWorkerError')"


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_successful_call(worker, full_runtests_params, job_extractor, monkeypatch, messages):
    monkeypatch.setattr(timezone, "now", lambda: datetime.datetime(2020, 1, 1))
    job = full_runtests_params.get_job()
    worker.job_extractor_factory = lambda: job_extractor
    worker.report_queryset.get.return_value = job.object
    worker(full_runtests_params)
    job.refresh_from_db()
    assert job.status == "completed"
    assert job.data == {
        "log": [
            *[m.serialized for m in messages],
            {
                "time": "2020-01-01T00:00:00",
                "status": "success",
                "message": "Job succeeded. See [Compliance Report](/plugins/validity/reports/1/) for detailed statistics",
            },
        ],
        "output": {"statistics": {"total": 7, "passed": 3}},
    }
    assert job.error == ""
    worker.enqueue_func.assert_called_once_with(job.object, full_runtests_params.request)
