import base64
from dataclasses import dataclass, field
from typing import ClassVar

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings


@dataclass
class EncryptedString:
    """
    The rudiment from Validity 1.x which was supposed to encrypt/decrypt passwords for GitRepo
    Now it is required to execute migration 0005
    """

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
    def from_plain_text(cls, message: str | bytes, salt: str | bytes):
        message = message.encode() if isinstance(message, str) else message
        salt = salt.encode() if isinstance(salt, str) else salt
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
        return (self.salt + b"$" + self.cipher).decode()

    @classmethod
    def deserialize(cls, value: str):
        salt, cipher = value.split("$")
        return cls(cipher.encode(), salt.encode())
