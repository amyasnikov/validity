from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

import boto3
from boto3.exceptions import Boto3Error

from validity.utils.misc import reraise
from .errors import IntegrationError


@dataclass(slots=True, frozen=True)
class S3URL:
    endpoint: str
    bucket: str
    key: str

    @classmethod
    def parse(cls, url: str):
        parsed_url = urlparse(url)
        path = parsed_url.path.lstrip("/")
        bucket, key = path.split("/", maxsplit=1) if "/" in path else path, ""
        return cls(parsed_url.netloc, bucket, key)


class S3Client(ABC):
    @abstractmethod
    def upload_file(self, path: Path, url: str, access_key_id: str, secret_access_key: str) -> None: ...

    @abstractmethod
    def upload_folder(self, path: Path, url: str, access_key_id: str, secret_access_key: str) -> None: ...


@dataclass
class BotoS3Client(S3Client):
    max_threads: int

    def _get_s3_client(self, endpoint: str, access_key_id: str, secret_access_key: str):
        return boto3.client(
            "s3", endpoint_url=endpoint, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key
        )

    def upload_file(self, path: Path, url: str | S3URL, access_key_id: str, secret_access_key: str) -> None:
        if not isinstance(url, S3URL):
            url = S3URL.parse(url)
        client = self._get_s3_client(url.endpoint, access_key_id, secret_access_key)
        with reraise(Boto3Error, IntegrationError):
            client.upload_file(path, url.bucket, url.key)

    def upload_folder(self, path: Path, url: str, access_key_id: str, secret_access_key: str) -> None:
        folder_url = S3URL.parse(url)
        futures = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for fs_obj in path.rglob("*"):
                if fs_obj.is_file():
                    file_url = replace(folder_url, key=str(fs_obj.relative_to(folder_url)))
                    fn = partial(self.upload_file(fs_obj, file_url, access_key_id, secret_access_key))
                    futures.append(executor.submit(fn))
            any(fut.result() for fut in futures)
