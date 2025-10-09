from http import HTTPStatus
from typing import Any
from unittest.mock import Mock

import pytest
from factories import CommandFactory, PollerFactory

from validity.dependencies import validity_settings
from validity.forms import PollerForm
from validity.models.polling import Command
from validity.pollers import CustomPoller
from validity.settings import PollerInfo, ValiditySettings


class MyCustomPoller(CustomPoller):
    host_param_name = "ip_address"
    driver_factory = Mock

    def poll_one_command(self, driver: Any, command: Command) -> str:
        return "output"


@pytest.fixture
def custom_poller(db, di):
    settings = ValiditySettings(
        custom_pollers=[
            PollerInfo(klass="test_custom_pollers.MyCustomPoller", name="cupo", color="red", command_types=["custom"])
        ]
    )
    with di.override({validity_settings: lambda: settings}):
        yield PollerFactory(connection_type="cupo")


def test_custom_poller_model(custom_poller, di):
    poller = PollerFactory(connection_type="cupo")
    poller.commands.set([CommandFactory(type="custom")])
    backend = poller.get_backend()
    assert isinstance(backend, MyCustomPoller)
    assert poller.get_connection_type_color() == "red"
    poller.validate_commands(poller.commands.all(), di["PollerChoices"].command_types, poller.connection_type)


def test_custom_poller_api(custom_poller, admin_client):
    resp = admin_client.get(f"/api/plugins/validity/pollers/{custom_poller.pk}/")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["connection_type"] == "cupo"


def test_custom_poller_form(custom_poller):
    form = PollerForm()
    form_choices = {choice[0] for choice in form["connection_type"].field.choices}
    assert "cupo" in form_choices
