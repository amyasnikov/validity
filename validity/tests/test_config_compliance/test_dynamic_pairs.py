from unittest.mock import Mock

import pytest
from django.db.models import Q
from factories import DeviceFactory, SelectorFactory

from validity.config_compliance.dynamic_pairs import DynamicNamePairFilter, NoneFilter, dpf_factory


@pytest.mark.parametrize("dynamic_pairs, filter_cls", [("NAME", DynamicNamePairFilter), ("NO", NoneFilter)])
def test_dpf_factory(dynamic_pairs, filter_cls):
    selector = Mock(dynamic_pairs=dynamic_pairs)
    obj = dpf_factory(selector=selector, device=Mock())
    assert type(obj) == filter_cls


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
    filter_ = DynamicNamePairFilter(selector, device)
    if dp_filter:
        assert filter_.filter == Q(name__regex=dp_filter)
    else:
        assert filter_.filter is None
