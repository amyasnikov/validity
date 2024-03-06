from typing import TYPE_CHECKING

import requests
from dcim.models import Device
from pydantic import BaseModel, Field

from validity.j2_env import Environment
from validity.utils.json import transform_json
from .base import ConsecutivePoller


if TYPE_CHECKING:
    from validity.models import Command, VDevice


class RequestParams(BaseModel, extra="allow"):
    url: str = Field(
        "https://{{device.primary_ip.address.ip}}/{{command.parameters.url_path.lstrip('/')}}", exclude=True
    )
    verify: bool | str = False
    auth: tuple[str, ...] | None = None

    def rendered_url(self, device: "Device", command: "Command") -> str:
        return Environment().from_string(self.url).render(device=device, command=command)


class HttpDriver:
    def __init__(self, device: Device, **poller_credentials) -> None:
        self.device = device
        self.request_params = RequestParams.model_validate(poller_credentials)

    def render_body(self, orig_body: dict, command: "Command"):
        return transform_json(
            orig_body,
            match_fn=lambda _, value: isinstance(value, str),
            transform_fn=lambda key, value: (
                key,
                Environment().from_string(value).render(device=self.device, command=command),
            ),
        )

    def request(self, command: "Command", *, requests=requests) -> str:
        request_kwargs = self.request_params.model_dump()
        request_kwargs["url"] = self.request_params.rendered_url(self.device, command)
        request_kwargs["method"] = command.parameters["method"]
        if body := self.render_body(command.parameters["body"], command):
            request_kwargs["json"] = body
        return requests.request(**request_kwargs).content.decode()


class RequestsPoller(ConsecutivePoller):
    driver_cls = HttpDriver

    def get_credentials(self, device: "VDevice"):
        return self.credentials | {"device": device}

    def poll_one_command(self, driver: HttpDriver, command: "Command") -> str:
        return driver.request(command)
