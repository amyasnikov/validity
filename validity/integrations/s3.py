from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from functools import partial
from pathlib import Path

import boto3
from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError

from validity.utils.misc import reraise
from .data_models import S3URL
from .errors import IntegrationError


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
        with reraise((Boto3Error, BotoCoreError), IntegrationError):
            client = self._get_s3_client(url.endpoint, access_key_id, secret_access_key)
            client.upload_file(path, url.bucket, url.key)

    def upload_folder(self, path: Path, url: str, access_key_id: str, secret_access_key: str) -> None:
        s3_url = S3URL.parse(url)
        futures = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for fs_obj in path.rglob("*"):
                if fs_obj.is_file():
                    file_path = s3_url.key / fs_obj.relative_to(path)
                    file_url = replace(s3_url, key=str(file_path))
                    fn = partial(self.upload_file, fs_obj, file_url, access_key_id, secret_access_key)
                    futures.append(executor.submit(fn))
            any(fut.result() for fut in futures)
