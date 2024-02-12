import json
from typing import TYPE_CHECKING

import jq
import requests
from dcim.models import Device
from pydantic import BaseModel, Field

from validity.j2_env import Environment
from validity.utils.misc import process_json_values, reraise
from .base import ConsecutivePoller
from .exceptions import PollingError


if TYPE_CHECKING:
    from validity.models import Command, VDevice


class RequestParams(BaseModel, extra="allow"):
    url: str = Field("https://{{device.primary_ip}}/{{command.parameters.url_path.lstrip('/')}}", exclude=True)
    verify: bool | str = False

    def rendered_url(self, device: "Device", command: "Command") -> str:
        return Environment().from_string(self.url).render(device=device, command=command)


class HttpDriver:
    def __init__(self, device: Device, **poller_credentials) -> None:
        self.device = device
        self.request_params = RequestParams.model_validate(poller_credentials)

    def render_body(self, orig_body: dict, command: "Command"):
        return process_json_values(
            orig_body,
            match_fn=lambda val: isinstance(val, str),
            transform_fn=lambda val: Environment().from_string(val).render(device=self.device, command=command),
        )

    def request(self, command: "Command") -> str:
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
        answer = driver.request(command)
        with reraise((json.JSONDecodeError, ValueError), PollingError, device_wide=False):
            json_answer = json.loads(answer)
            if jq_query := command.parameters.get("jq_query"):
                json_answer = jq.first(jq_query, json_answer)
            return json.dumps(json_answer)
