from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, Mock

import pytest
from core.choices import DataSourceStatusChoices
from core.models import DataSource
from factories import CommandFactory, DataFileFactory, DataSourceFactory, DeviceFactory

from validity.models import VDataFile, VDataSource


@pytest.mark.django_db
def test_sync_status():
    data_source = DataSourceFactory()
    assert data_source.status != DataSourceStatusChoices.SYNCING
    with data_source._sync_status():
        assert data_source.status == DataSourceStatusChoices.SYNCING
        assert VDataSource.objects.get(pk=data_source.pk).status == DataSourceStatusChoices.SYNCING
    assert data_source.status == DataSourceStatusChoices.COMPLETED
    assert VDataSource.objects.get(pk=data_source.pk).status == DataSourceStatusChoices.COMPLETED

    with suppress(Exception):
        with data_source._sync_status():
            raise ValueError
    assert data_source.status == DataSourceStatusChoices.FAILED
    assert VDataSource.objects.get(pk=data_source.pk).status == DataSourceStatusChoices.FAILED


@pytest.mark.django_db
def test_partial_sync(monkeypatch):
    ds = DataSourceFactory(type="device_polling")
    DataFileFactory(source=ds, data="some_contents".encode(), path="file-0.txt")
    DataFileFactory(source=ds, path="file-1.txt")
    with TemporaryDirectory() as temp_dir:
        existing = Path(temp_dir) / "file-1.txt"
        new = Path(temp_dir) / "file_new.txt"
        existing.write_text("qwe")
        new.write_text("rty")
        fetch_mock = MagicMock(**{"return_value.fetch.return_value.__enter__.return_value": temp_dir})
        monkeypatch.setattr(ds, "get_backend", fetch_mock)
        ds.partial_sync("device_filter")
        fetch_mock().fetch.assert_called_once_with("device_filter")
        assert {*ds.datafiles.values_list("path", flat=True)} == {"file-0.txt", "file-1.txt", "file_new.txt"}
        assert VDataFile.objects.get(path="file-0.txt").data_as_string == "some_contents"
        assert VDataFile.objects.get(path="file-1.txt").data_as_string == "qwe"
        assert VDataFile.objects.get(path="file_new.txt").data_as_string == "rty"
        assert VDataSource.objects.get(pk=ds.pk).status == DataSourceStatusChoices.COMPLETED


@pytest.mark.django_db
def test_sync_with_param(monkeypatch):
    ds = DataSourceFactory(type="device_polling")
    monkeypatch.setattr(DataSource, "sync", Mock())
    monkeypatch.setattr(VDataSource, "partial_sync", Mock())
    ds.sync()
    DataSource.sync.assert_called_once_with()
    assert VDataSource.partial_sync.call_count == 0
    filtr = object()
    ds.sync(filtr)
    VDataSource.partial_sync.assert_called_once_with(filtr)


@pytest.mark.django_db
def test_get_path(create_custom_fields):
    device = DeviceFactory(name="device 1")
    command = CommandFactory(label="cmd1")
    ds = DataSourceFactory(
        custom_field_data={
            "web_url": "http://ex.com/{{branch}}",
            "device_config_path": "cfg/{{device.name}}.cfg",
            "device_command_path": "state/{{device | slugify}}/{{command.label}}.txt",
        },
        parameters={"branch": "b1"},
    )
    assert ds.web_url == "http://ex.com/b1"
    assert ds.get_config_path(device) == "cfg/device 1.cfg"
    assert ds.get_command_path(device, command) == "state/device-1/cmd1.txt"
