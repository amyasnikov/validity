import pytest
from factories import PollerFactory

from validity.pollers import NetmikoPoller, RequestsPoller, ScrapliNetconfPoller


@pytest.mark.parametrize(
    "connection_type, poller_class",
    [("netmiko", NetmikoPoller), ("requests", RequestsPoller), ("scrapli_netconf", ScrapliNetconfPoller)],
)
@pytest.mark.django_db
def test_get_backend(connection_type, poller_class):
    poller = PollerFactory(connection_type=connection_type)
    backend = poller.get_backend()
    assert isinstance(backend, poller_class)
