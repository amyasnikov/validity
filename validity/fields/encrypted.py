import base64
import os
import pickle
from dataclasses import dataclass, field
from typing import Any, ClassVar

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Field, JSONField


@dataclass
class EncryptedString:
    cipher: bytes
    salt: bytes
    _fernet: Fernet | None = field(default=None, compare=False, repr=False)

    secret_key: ClassVar[bytes] = settings.SECRET_KEY.encode()

    def __post_init__(self):
        if self._fernet is None:
            self._fernet = self.get_fernet(base64.urlsafe_b64decode(self.salt))

    def __len__(self) -> int:
        return len(self.cipher)

    @classmethod
    def from_plain_text(cls, message: str | bytes, salt: bytes = b""):
        message = message.encode() if isinstance(message, str) else message
        salt = salt or os.urandom(16)
        fernet = cls.get_fernet(salt)
        cipher = fernet.encrypt(message)
        return cls(cipher, base64.urlsafe_b64encode(salt), fernet)

    @classmethod
    def get_fernet(cls, salt: bytes) -> Fernet:
        if isinstance(salt, str):
            salt = salt.encode()
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000, backend=default_backend())
        return Fernet(base64.urlsafe_b64encode(kdf.derive(cls.secret_key)))

    def decrypt(self) -> str:
        return self._fernet.decrypt(self.cipher).decode()

    def serialize(self) -> str:
        return f"${self.salt.decode()}${self.cipher.decode()}$"

    @classmethod
    def deserialize(cls, value: str):
        salt, cipher = value.strip("$").split("$")
        return cls(cipher.encode(), salt.encode())


class EncryptedObject(EncryptedString):
    @classmethod
    def from_object(cls, obj: Any, salt: bytes = b""):
        return super().from_plain_text(pickle.dumps(obj), salt)

    def decrypt(self) -> Any:
        return pickle.loads(self._fernet.decrypt(self.cipher))


class EncryptedDict(dict):
    def __init__(self, iterable=()):
        super().__init__()
        if isinstance(iterable, dict):
            iterable = iterable.items()
        for k, v in iterable:
            constructor = EncryptedObject.from_object
            if isinstance(v, str) and len(v) > 3 and v.startswith("$") and v.endswith("$"):
                constructor = EncryptedObject.deserialize
            self[k] = constructor(v)

    @property
    def encrypted(self) -> dict:
        return {k: v.serialize() for k, v in self.items()}

    @property
    def decrypted(self) -> dict:
        return {k: v.decrypt() for k, v in self.items()}


class EncryptedFieldEncoder(DjangoJSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, EncryptedString):
            return o.serialize()
        return super().default(o)


class EncryptedDictField(JSONField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("default", EncryptedDict)
        kwargs["encoder"] = EncryptedFieldEncoder
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> Any:
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get("default") == EncryptedDict:
            del kwargs["default"]
        del kwargs["encoder"]
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        if isinstance(value, dict):
            return EncryptedDict(value)

    def get_prep_value(self, value: dict | None) -> dict | None:
        if isinstance(value, EncryptedDict):
            value = value.encrypted
        if isinstance(value, dict):
            value = EncryptedDict(value).encrypted
        return super().get_prep_value(value)

    def to_python(self, value):
        if value is None or isinstance(value, EncryptedDict):
            return value
        return EncryptedDict(value)

    def formfield(self, **kwargs):
        from validity.forms.helpers import EncryptedDictField as EncryptedDictFormField

        return Field.formfield(
            self,
            **{
                "form_class": EncryptedDictFormField,
                "encoder": self.encoder,
                "decoder": self.decoder,
                **kwargs,
            },
        )

    def value_to_string(self, obj: Any) -> Any:
        return super().value_to_string(obj).encrypted
