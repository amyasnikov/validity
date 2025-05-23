import datetime
from itertools import chain
from unittest.mock import Mock

import factory
import pytest
from django.db.models import Q
from django.db.models.signals import post_save
from django.utils import timezone
from factories import (
    BackupPointFactory,
    DataSourceFactory,
    DeviceFactory,
    RunTestsJobFactory,
    SelectorFactory,
    TenantFactory,
)

from validity.data_backup import BackupBackend
from validity.integrations.errors import IntegrationError
from validity.models import VDataSource
from validity.scripts.data_models import Message, SplitResult
from validity.scripts.runtests.split import SplitWorker
from validity.utils.logger import Logger


@pytest.fixture
@factory.django.mute_signals(post_save)
def selectors(db):
    s1 = SelectorFactory(name_filter="g1-.*")
    s2 = SelectorFactory(name_filter="g2-.*")
    return s1, s2


@pytest.fixture
@factory.django.mute_signals(post_save)
def devices(device_num):
    for i in range(device_num // 2):
        DeviceFactory(name=f"g1-{i}")
    for i in range(device_num // 2, device_num):
        DeviceFactory(name=f"g2-{i}")


@pytest.fixture
def split_worker():
    return SplitWorker()


@pytest.mark.parametrize(
    "worker_num, device_num, expected_result",
    [
        (1, 6, [{1: [1, 2, 3], 2: [4, 5, 6]}]),
        (2, 6, [{1: [1, 2, 3]}, {2: [4, 5, 6]}]),
        (3, 6, [{1: [1, 2]}, {1: [3], 2: [4]}, {2: [5, 6]}]),
        (2, 3, [{1: [1], 2: [3]}, {2: [2]}]),
        (5, 9, [{1: [1], 2: [6]}, {1: [2], 2: [7]}, {1: [3], 2: [8]}, {1: [4], 2: [9]}, {2: [5]}]),
    ],
)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
@factory.django.mute_signals(post_save)
def test_distribute_work(split_worker, selectors, worker_num, runtests_params, expected_result, devices):
    # this test is unstable due to unpredictable db obj extraction order
    runtests_params.workers_num = worker_num
    runtests_params.selectors = [s.pk for s in selectors]
    result = split_worker.distribute_work(runtests_params, Logger(), runtests_params.get_device_filter())
    assert result == expected_result


@pytest.mark.parametrize(
    "worker_num, device_num",
    [
        (2, 5),
        (3, 5),
        (4, 5),
        (5, 5),
    ],
)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
@factory.django.mute_signals(post_save)
def test_distribute_work_2(split_worker, selectors, worker_num, runtests_params, devices, device_num):
    runtests_params.workers_num = worker_num
    runtests_params.selectors = [s.pk for s in selectors]
    result = split_worker.distribute_work(runtests_params, Logger(), runtests_params.get_device_filter())
    assert len(result) <= worker_num
    all_devices = list(chain.from_iterable([v for dictt in result for _, v in dictt.items()]))
    all_selectors = {k for dictt in result for k, _ in dictt.items()}
    assert len(all_devices) == device_num and set(all_devices) == {*range(1, device_num + 1)}
    assert all_selectors == {1, 2}


@pytest.mark.parametrize("overriding_datasource", [None, DataSourceFactory])
@pytest.mark.django_db
def test_sync_datasources(create_custom_fields, overriding_datasource):
    if overriding_datasource:
        overriding_datasource = overriding_datasource()
    ds1 = DataSourceFactory()
    ds2 = DataSourceFactory()
    DataSourceFactory()
    DeviceFactory(name="d1", tenant=TenantFactory(custom_field_data={"data_source": ds1.pk}))
    DeviceFactory(name="d2", tenant=TenantFactory(custom_field_data={"data_source": ds2.pk}))
    DeviceFactory()

    worker = SplitWorker(datasource_sync_fn=Mock())
    overriding_pk = overriding_datasource.pk if overriding_datasource else None
    logger = Mock()
    worker.sync_datasources(overriding_pk, device_filter=Q(name__in=["d1", "d2"]), logger=logger)
    worker.datasource_sync_fn.assert_called_once()
    datasources, device_filter = worker.datasource_sync_fn.call_args.args
    assert device_filter == Q(name__in=["d1", "d2"])
    expected_result = [overriding_datasource] if overriding_datasource else [ds1, ds2]
    assert list(datasources) == expected_result
    logger.info.assert_called_once()


@pytest.mark.django_db
def test_backup_datasources_success():
    backup_fn = Mock()
    bp1 = BackupPointFactory(backup_after_sync=True, name="bp1")
    worker = SplitWorker(backup_fn=backup_fn)
    worker.backup_datasources(VDataSource.objects.all(), Logger())
    backup_fn.assert_called_once()
    assert backup_fn.call_args[0][0] == {bp1}


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_backup_datasources_fail(timezone_now, di):
    timezone_now(datetime.datetime(2000, 1, 2, 3, 4, tzinfo=datetime.timezone.utc))
    bp = BackupPointFactory(backup_after_sync=True, name="bp1")
    worker = SplitWorker()
    backend = Mock(side_effect=IntegrationError("ERR123"))
    with di.override({BackupBackend: lambda: backend}):
        worker.backup_datasources(VDataSource.objects.all(), logger := Logger())
    backend.assert_called_once_with(bp)
    assert logger.messages == [
        Message(
            status="failure",
            message="Cannot back up [bp1](/plugins/validity/backup-points/1/). ERR123",
            time=datetime.datetime(2000, 1, 2, 3, 4, tzinfo=datetime.timezone.utc),
        )
    ]


@pytest.mark.parametrize("device_num", [2])
@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_call(selectors, devices, runtests_params, monkeypatch):
    time = timezone.datetime(year=2000, month=1, day=1, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr(timezone, "now", lambda: time)
    job = RunTestsJobFactory()
    runtests_params = runtests_params.with_job_info(job)
    runtests_params.workers_num = 2
    runtests_params.sync_datasources = True
    runtests_params.selectors = [s.pk for s in selectors]
    worker = SplitWorker(datasource_sync_fn=Mock())
    result = worker(runtests_params)
    assert result == SplitResult(
        log=[
            Message(
                status="warning",
                message="No bound Data Sources found. Sync skipped",
                time=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
            ),
            Message(
                status="info",
                message="Running the tests for *2 devices*",
                time=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
            ),
            Message(
                status="info",
                message="Distributing the work among 2 workers. Each worker handles 1 device(s) in average",
                time=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
            ),
        ],
        slices=[{1: [1]}, {2: [2]}],
    )
    assert worker.datasource_sync_fn.call_count == 0
    job.refresh_from_db()
    assert job.status == "running"
