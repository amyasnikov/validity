from unittest.mock import Mock

import pytest
from django.db.models import Q
from factories import (
    DeviceFactory,
    DeviceTypeFactory,
    LocationFactory,
    ManufacturerFactory,
    PlatformFactory,
    SelectorFactory,
    SiteFactory,
    TagFactory,
)

from validity.models import VDevice, selector


@pytest.mark.parametrize(
    "attr, attr_value, filter_operation, expected_filter",
    [
        ("name_filter", "some_name", "AND", "(AND: ('name__regex', 'some_name'))"),
        ("tag_filter", [TagFactory, TagFactory], "AND", "(OR: ('tags', <Tag: tag-0>), ('tags', <Tag: tag-1>))"),
        (
            "manufacturer_filter",
            [ManufacturerFactory],
            "AND",
            "(AND: ('device_type__manufacturer', <Manufacturer: manufacturer-0>))",
        ),
        ("type_filter", [DeviceTypeFactory], "AND", "(AND: ('device_type', <DeviceType: model-0>))"),
        ("platform_filter", [PlatformFactory], "OR", "(AND: ('platform', <Platform: platform-0>))"),
        ("status_filter", "ACTIVE", "OR", "(AND: ('status', 'ACTIVE'))"),
        ("location_filter", [LocationFactory], "AND", "(AND: ('location', <Location: location-0>))"),
        ("site_filter", [SiteFactory], "AND", "(AND: ('site', <Site: site-0>))"),
    ],
)
@pytest.mark.django_db
def test_filter(attr, attr_value, filter_operation, expected_filter):
    model = SelectorFactory()
    if isinstance(attr_value, list):
        for i, m in enumerate(attr_value):
            attr_value[i] = m(__sequence=i)
        getattr(model, attr).set(attr_value)
    else:
        setattr(model, attr, attr_value)
        model.save()
    assert str(model.filter) == expected_filter


@pytest.mark.django_db
def test_multi_filter():
    model = SelectorFactory()
    model.name_filter = "some_name"
    model.site_filter.set([SiteFactory(__sequence=0), SiteFactory(__sequence=1)])
    model.save()
    assert (
        str(model.filter)
        == "(AND: ('name__regex', 'some_name'), (OR: ('site', <Site: site-0>), ('site', <Site: site-1>)))"
    )


@pytest.mark.django_db
def test_devices(monkeypatch):
    monkeypatch.setattr(VDevice.objects, "filter", filter_mock := Mock(name="filter"))
    monkeypatch.setattr(selector.ComplianceSelector, "filter", "filter_value")
    model = SelectorFactory()
    assert model.devices._extract_mock_name() == "filter().set_selector()"
    filter_mock.assert_called_once_with("filter_value")


@pytest.mark.django_db
def test_dynamic_pairs(monkeypatch):
    monkeypatch.setattr(selector, "dpf_factory", dpf_mock := Mock(return_value=Mock(filter=Q(dpf_filter=True))))
    selector_instance = SelectorFactory()
    device = DeviceFactory()
    dp_filter = selector_instance.dynamic_pair_filter(device)
    dpf_mock.assert_called_once_with(selector_instance, device)
    assert dp_filter == Q(dpf_filter=True) & ~Q(pk=device.pk)
