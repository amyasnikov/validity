import datetime

import pytest
from factories import DSBackupJobFactory

from validity.netbox_changes import get_logs
from validity.scripts.exceptions import AbortScript
from validity.scripts.keeper import JobKeeper
from validity.utils.logger import Logger, Message


@pytest.mark.django_db
def test_keeper_noerror(timezone_now):
    timezone_now(datetime.datetime(2000, 1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc))
    with JobKeeper(job=DSBackupJobFactory(), logger=Logger()) as keeper:
        assert keeper.job.status == "running"
        keeper.logger.info("msg")
    keeper.job.refresh_from_db()
    assert keeper.job.status == "completed"
    assert get_logs(keeper.job) == [{"time": "2000-01-01T01:00:00+00:00", "status": "info", "message": "msg"}]
    assert keeper.logger.messages == []


@pytest.mark.django_db
def test_keeper_abort(timezone_now):
    timezone_now(datetime.datetime(2000, 1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc))
    with JobKeeper(job=DSBackupJobFactory(), logger=Logger()) as keeper:
        keeper.logger.info("msg1")
        raise AbortScript("abort_msg", logs=[Message("warning", "extra_msg")])
    keeper.job.refresh_from_db()
    assert keeper.job.status == "failed"
    assert get_logs(keeper.job) == [
        {"time": "2000-01-01T01:00:00+00:00", "status": "info", "message": "msg1"},
        {"time": "2000-01-01T01:00:00+00:00", "status": "warning", "message": "extra_msg"},
        {"time": "2000-01-01T01:00:00+00:00", "status": "failure", "message": "abort_msg"},
    ]
    assert keeper.logger.messages == []


@pytest.mark.django_db
def test_keeper_exception(timezone_now):
    timezone_now(datetime.datetime(2000, 1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc))
    with pytest.raises(ValueError):
        with JobKeeper(job=DSBackupJobFactory(), logger=Logger()) as keeper:
            keeper.logger.info("msg1")
            raise ValueError("unexpected")
    keeper.job.refresh_from_db()
    assert keeper.job.status == "errored"
    logs = get_logs(keeper.job)
    assert len(logs) == 2
    assert logs[0] == {"time": "2000-01-01T01:00:00+00:00", "status": "info", "message": "msg1"}
    assert logs[1]["status"] == "failure"
    assert logs[1]["message"].startswith("Unhandled error occured: `<class 'ValueError'>: unexpected")
    assert keeper.logger.messages == []
