from typing import Annotated

from pydantic import BaseModel, Field

from validity import di


class WorkerTimeouts(BaseModel):
    split: int | str = "15m"
    apply: int | str = "30m"
    combine: int | str = "15m"
    rollback: int | str = "5m"


class ValiditySettings(BaseModel):
    store_last_results: int = Field(default=5, gt=0, lt=1001)
    store_reports: int = Field(default=5, gt=0, lt=1001)
    result_batch_size: int = Field(default=500, ge=1)
    polling_threads: int = Field(default=500, ge=1)
    worker_timeouts: WorkerTimeouts = WorkerTimeouts()


class ValiditySettingsMixin:
    @property
    @di.inject
    def v_settings(self, _settings: Annotated[ValiditySettings, "validity_settings"]) -> ValiditySettings:
        return _settings
