from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from validity.integrations.data_models import S3URL
from validity.integrations.s3 import BotoS3Client


class MockBotoClient(BotoS3Client):
    _m = Mock()

    def _get_s3_client(self, endpoint, access_key_id, secret_access_key):
        return self._m(endpoint, access_key_id, secret_access_key)


class SuperMockBotoClient(BotoS3Client):
    _m = Mock()

    def upload_file(self, path, url, access_key_id, secret_access_key):
        return self._m(path, url, access_key_id, secret_access_key)


def test_upload_file():
    client = MockBotoClient(10)
    client.upload_file(
        path=Path("/tmp"), url="https://aws.com/mybucket/folder/file.txt", access_key_id="12", secret_access_key="34"
    )
    client._m.assert_called_once_with("https://aws.com", "12", "34")
    client._m.return_value.upload_file.assert_called_once_with(Path("/tmp"), "mybucket", "folder/file.txt")


def test_upload_folder():
    client = SuperMockBotoClient(10)
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        f1 = tmpdir / "f1.txt"
        f2 = tmpdir / "fldr" / "f2.txt"
        f1.touch()
        f2.parent.mkdir()
        f2.touch()
        client.upload_folder(tmpdir, "https://aws.com/mybucket/folder", "12", "34")
        assert client._m.call_count == 2
        client._m.assert_any_call(f1, S3URL.parse("https://aws.com/mybucket/folder/f1.txt"), "12", "34")
        client._m.assert_any_call(f2, S3URL.parse("https://aws.com/mybucket/folder/fldr/f2.txt"), "12", "34")
