from unittest.mock import Mock

import pytest
from django.db.models import Q
from extras.models import Tag
from factories import DeviceFactory, SelectorFactory, TagFactory

from validity.compliance.dynamic_pairs import DynamicPairNameFilter, DynamicPairTagFilter, NoneFilter, dpf_factory


@pytest.mark.parametrize(
    "dynamic_pairs, filter_cls",
    [
        ("NAME", DynamicPairNameFilter),
        ("NO", NoneFilter),
        ("TAG", DynamicPairTagFilter),
    ],
)
def test_dpf_factory(dynamic_pairs, filter_cls):
    selector = Mock(dynamic_pairs=dynamic_pairs)
    obj = dpf_factory(selector=selector, device=Mock())
    assert isinstance(obj, filter_cls)


@pytest.mark.parametrize(
    "name_filter, device_name, dp_filter",
    [
        pytest.param("asw[0-9]+-([ab])", "asw01-a.london", "asw01-([ab]).london", id="asw01-([ab]).london"),
        pytest.param("sw[0-9]+-(first|second)", "sw05-second", "sw05-(first|second)", id="sw05-(first|second)"),
        pytest.param(r"sw[0-9]+-\([12]\)", "sw01-1", None, id="None1"),
        pytest.param("sw[0-9]+-(?:[12])", "sw01-1", None, id="None2"),
        pytest.param("sw[0-9]+-[12]", "sw01-1", None, id="None3"),
        pytest.param("sw[()0-9]+-([12])", "ny-sw01-1", "ny-sw01-([12])", id="ny-sw01-([12])"),
        pytest.param("sw[0-9]+-([12])-([a-z]+)", "sw01-1-paris", "sw01-([12])-paris", id="sw01-([12])-paris"),
    ],
)
@pytest.mark.django_db
def test_name_filter(name_filter, device_name, dp_filter):
    device = DeviceFactory(name=device_name)
    selector = SelectorFactory(name_filter=name_filter)
    filter_ = DynamicPairNameFilter(selector, device)
    if dp_filter:
        assert filter_.filter == Q(name__regex=dp_filter)
    else:
        assert filter_.filter is None


@pytest.mark.django_db
def test_tag_filter():
    tags = [
        TagFactory(name="tag-1_", slug="tag-1"),
        TagFactory(name="tag-2_", slug="tag-2"),
        TagFactory(name="sometag_", slug="sometag"),
    ]
    selector = SelectorFactory(dp_tag_prefix="tag-", name_filter=".*")
    device = DeviceFactory()
    device.tags.set([tags[0], tags[2]])
    filter_ = DynamicPairTagFilter(selector, device).filter
    assert repr(filter_) == repr(Q(tags__in=Tag.objects.filter(slug="tag-1")))
