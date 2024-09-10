from typing import Annotated

from pydantic import BaseModel, Field

from validity import di


class ScriptTimeouts(BaseModel):
    """
    Timeout syntax complies with rq timeout format
    """

    runtests_split: int | str = "10m"
    runtests_apply: int | str = "30m"
    runtests_combine: int | str = "10m"


class ValiditySettings(BaseModel):
    store_reports: int = Field(default=5, gt=0, lt=1001)
    result_batch_size: int = Field(default=500, ge=1)
    polling_threads: int = Field(default=500, ge=1)
    runtests_queue: str = "default"
    script_timeouts: ScriptTimeouts = ScriptTimeouts()


class ValiditySettingsMixin:
    @property
    @di.inject
    def v_settings(self, _settings: Annotated[ValiditySettings, "validity_settings"]) -> ValiditySettings:
        return _settings
