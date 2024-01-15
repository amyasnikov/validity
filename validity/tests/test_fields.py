import pytest

from validity.fields import EncryptedDict, EncryptedString


@pytest.fixture
def setup_private_key(monkeypatch):
    monkeypatch.setattr(EncryptedString, "secret_key", b"1234567890")


@pytest.mark.parametrize(
    "plain_value",
    [
        {"param1": "val1", "param2": "val2"},
        {},
        {"param": ["some", "complex", {"val": "ue"}]},
    ],
)
def test_encrypted_dict(plain_value, setup_private_key):
    enc_dict = EncryptedDict(plain_value)
    assert enc_dict.decrypted == plain_value
    assert enc_dict.keys() == enc_dict.encrypted.keys() == plain_value.keys()
    assert all(val.startswith("$") and val.endswith("$") and val.count("$") == 3 for val in enc_dict.encrypted.values())
    assert EncryptedDict(enc_dict.encrypted).decrypted == plain_value
