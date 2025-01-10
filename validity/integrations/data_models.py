from dataclasses import dataclass
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict


class GitFileChange(BaseModel):
    add: list[str]
    delete: list[str]
    modify: list[str]

    @property
    def has_changes(self) -> bool:
        return self.add or self.delete or self.modify


class GitStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staged: GitFileChange
    unstaged: list[str]
    untracked: list[str]

    @property
    def has_changes(self) -> bool:
        return self.staged.has_changes or self.unstaged or self.untracked


@dataclass(slots=True, frozen=True)
class S3URL:
    endpoint: str
    bucket: str
    key: str  # file path inside the bucket

    @classmethod
    def parse(cls, url: str):
        parsed_url = urlparse(url)
        path = parsed_url.path.lstrip("/")
        bucket, key = path.split("/", maxsplit=1) if "/" in path else (path, "")
        endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return cls(endpoint, bucket, key)
