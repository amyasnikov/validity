import datetime
from zoneinfo import ZoneInfo

import pytest
from dcim.models import Device
from django.db.models import Q
from factories import CompTestDBFactory, DeviceFactory, SelectorFactory, TagFactory

from validity.scripts import data_models


def test_serialized_message():
    time = datetime.datetime(year=2000, month=2, day=3, hour=14, minute=10, second=35, tzinfo=ZoneInfo("UTC"))
    msg = data_models.Message(status="info", message="hello", time=time)
    assert msg.serialized == {"status": "info", "message": "hello", "time": "2000-02-03T14:10:35+00:00"}

    msg2 = data_models.Message(status="info", message="hello2", time=time, script_id="My Script")
    assert msg2.serialized["message"] == "My Script, hello2"


def test_resultratio_sum():
    r1 = data_models.TestResultRatio(passed=1, total=5)
    r2 = data_models.TestResultRatio(passed=3, total=3)
    r3 = data_models.TestResultRatio(passed=0, total=1)

    assert r1 + r2 == data_models.TestResultRatio(4, 8)
    assert r1 + r2 + r3 == data_models.TestResultRatio(4, 9)


class TestRunTestsParams:
    @pytest.fixture
    def selectors(self, db):
        return [SelectorFactory() for _ in range(10)]

    def test_selector_qs(self, runtests_params, selectors):
        assert list(runtests_params.selector_qs) == selectors

        runtests_params.selectors = [selectors[0].id, selectors[2].id]
        assert list(runtests_params.selector_qs) == [selectors[0], selectors[2]]

    def test_selector_qs_with_tags(self, runtests_params, selectors):
        tag1 = TagFactory()
        tag2 = TagFactory()
        test1 = CompTestDBFactory()
        test1.tags.add(tag1)
        test2 = CompTestDBFactory()
        test2.tags.add(tag2)

        test1.selectors.set([selectors[0], selectors[1]])
        test2.selectors.set([selectors[1], selectors[2], selectors[3]])
        runtests_params.test_tags = [test1.pk, test2.pk]
        assert list(runtests_params.selector_qs) == selectors[:4]

        runtests_params.selectors = [selectors[0].pk, selectors[6].pk]

        assert list(runtests_params.selector_qs) == [selectors[0]]

    @pytest.mark.django_db
    def test_get_device_filter_empty_selectors(self, params):
        assert params.get_device_filter() == Q(pk__in=[])

    @pytest.mark.django_db
    def test_get_device_filter_with_selectors(self, runtests_params, selectors):
        selectors[0].name_filter = "g1-.*"
        selectors[0].save()
        selectors[1].name_filter = "g2-.*"
        selectors[1].save()
        d1 = DeviceFactory(name="g1-dev1")
        DeviceFactory(name="g1-dev2")
        DeviceFactory(name="g2-dev1")
        d2 = DeviceFactory(name="some_device")
        runtests_params.selectors = [selectors[0].pk, selectors[1].pk]
        device_filter = runtests_params.get_device_filter()
        assert {*Device.objects.filter(device_filter).values_list("name", flat=True)} == {
            "g1-dev1",
            "g1-dev2",
            "g2-dev1",
        }

        runtests_params.devices = [d1.pk, d2.pk]
        device_filter = runtests_params.get_device_filter()
        assert {*Device.objects.filter(device_filter).values_list("name", flat=True)} == {"g1-dev1"}
