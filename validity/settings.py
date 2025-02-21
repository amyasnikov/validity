from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validity import di
from validity.pollers import BasePoller


class ScriptTimeouts(BaseModel):
    """
    Timeout syntax complies with rq timeout format
    """

    runtests_split: int | str = "10m"
    runtests_apply: int | str = "30m"
    runtests_combine: int | str = "10m"
    backup: int | str = "10m"


class PollerInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    klass: type[BasePoller] = Field(validation_alias="class")
    name: str = Field(pattern="[a-z_]+")
    verbose_name: str = Field(default="", validate_default=True)
    color: str = Field(pattern="[a-z-]+")
    command_types: list[Literal["CLI", "netconf", "json_api", "custom"]]

    @field_validator("verbose_name")
    @classmethod
    def validate_verbose_name(cls, value, info):
        if value:
            return value
        return " ".join(part.title() for part in info.data["name"].split("_"))


class GitSettings(BaseModel):
    author: str = "netbox-validity"
    email: str = "validity@netbox.local"


class S3Settings(BaseModel):
    threads: int = 10


class IntegrationSettings(BaseModel):
    s3: S3Settings = S3Settings()
    git: GitSettings = GitSettings()


class CustomQueueSettings(BaseModel):
    runtests: str = "default"
    backup: str = "default"


class ValiditySettings(BaseModel):
    store_reports: int = Field(default=5, gt=0, lt=1001)
    result_batch_size: int = Field(default=500, ge=1)
    polling_threads: int = Field(default=500, ge=1)
    custom_queues: CustomQueueSettings = CustomQueueSettings()
    script_timeouts: ScriptTimeouts = ScriptTimeouts()
    custom_pollers: list[PollerInfo] = []
    integrations: IntegrationSettings = IntegrationSettings()
    top_level_menu: bool = True

    @model_validator(mode="before")
    @classmethod
    def extract_legacy_runtests_queue(cls, values):
        if runtests_queue := values.get("runtests_queue"):
            values.setdefault("custom_queues", {})
            values["custom_queues"].setdefault("runtests", runtests_queue)
        return values


class ValiditySettingsMixin:
    @property
    @di.inject
    def v_settings(self, _settings: Annotated[ValiditySettings, "validity_settings"]) -> ValiditySettings:
        return _settings
