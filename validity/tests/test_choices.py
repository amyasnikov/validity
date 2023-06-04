from unittest.mock import Mock

import pytest

from validity.choices import SeverityChoices


@pytest.mark.parametrize(
    "query_param, choice",
    [
        (None, SeverityChoices.LOW),
        ("invalid_value", SeverityChoices.LOW),
        ("LOW", SeverityChoices.LOW),
        ("middle", SeverityChoices.MIDDLE),
        ("HIGH", SeverityChoices.HIGH),
    ],
)
def test_severity_from_request(query_param, choice):
    request = Mock(**{"GET.get.return_value": query_param})
    assert SeverityChoices.from_request(request) is choice


@pytest.mark.parametrize(
    "severity, result",
    [
        (SeverityChoices.LOW, ["LOW", "MIDDLE", "HIGH"]),
        (SeverityChoices.MIDDLE, ["MIDDLE", "HIGH"]),
        (SeverityChoices.HIGH, ["HIGH"]),
    ],
)
def test_severity_ge(severity, result):
    assert SeverityChoices.ge(severity) == result
