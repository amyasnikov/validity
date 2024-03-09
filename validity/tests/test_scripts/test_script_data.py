import pytest
from django.db.models import Q
from factories import SelectorFactory

from validity.models import ComplianceSelector
from validity.scripts.script_data import RunTestsScriptData


@pytest.fixture
def mkpatch_selector_filter(monkeypatch):
    def get_filter(self):
        nonlocal counter
        counter += 1
        return Q(pk=counter)

    counter = 100
    monkeypatch.setattr(ComplianceSelector, "filter", property(get_filter))


@pytest.mark.parametrize(
    "selectors, devices, result",
    [
        ([], [], Q()),
        ([SelectorFactory, SelectorFactory], [], Q(pk=101) | Q(pk=102)),
        ([], [10, 11, 12], Q(pk=10) | Q(pk=11) | Q(pk=12)),
        ([SelectorFactory, SelectorFactory], [21, 22], (Q(pk=101) | Q(pk=102)) & (Q(pk=21) | Q(pk=22))),
    ],
)
@pytest.mark.django_db
def test_get_filter(selectors, devices, result, mkpatch_selector_filter):
    selectors = [s().pk for s in selectors]
    script_data = RunTestsScriptData({"selectors": selectors, "devices": devices})
    assert script_data.device_filter == result
