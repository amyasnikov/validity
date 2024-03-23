"""
Models from this module are used by js script to render default credentials for a new poller in UI
"""

from typing import Any

from pydantic import BaseModel


class EmptyCredentials(BaseModel):
    pass


class NetmikoPublicCreds(BaseModel):
    device_type: str = ""
    username: str = ""


class NetmikoPrivateCreds(BaseModel):
    password: str = ""


class ScrapliNeconfPublicCreds(BaseModel):
    auth_username: str = ""
    auth_strict_key: bool = False
    port: int = 830


class ScrapliNeconfPrivateCreds(BaseModel):
    auth_password: str = ""


class RequestsPublicCreds(BaseModel):
    url: str = "https://{{device.primary_ip.address.ip}}/{{command.parameters.url_path.lstrip('/')}}"


class ConnectionTypeCredentials(BaseModel):
    public: Any
    private: Any


class AllCredentials(BaseModel):
    netmiko: ConnectionTypeCredentials
    scrapli_netconf: ConnectionTypeCredentials
    requests: ConnectionTypeCredentials


all_credentials = AllCredentials(
    netmiko=ConnectionTypeCredentials(public=NetmikoPublicCreds(), private=NetmikoPrivateCreds()),
    scrapli_netconf=ConnectionTypeCredentials(public=ScrapliNeconfPublicCreds(), private=ScrapliNeconfPrivateCreds()),
    requests=ConnectionTypeCredentials(public=RequestsPublicCreds(), private=EmptyCredentials()),
)
