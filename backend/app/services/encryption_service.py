"""Encryption service for securing credentials at rest."""
import base64
import hashlib
import logging
import os
import secrets
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    _instance: Optional["EncryptionService"] = None
    _fernet: Optional[Fernet] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._fernet is None:
            self._initialize()

    def _initialize(self) -> None:
        """Initialize the encryption key from environment or generate new."""
        from app.config import get_settings
        settings = get_settings()

        key = settings.encryption_key

        if key:
            self._fernet = Fernet(self._derive_key(key))
            logger.info("Encryption service initialized with provided key")
        else:
            new_key = Fernet.generate_key()
            self._fernet = Fernet(new_key)
            logger.warning(
                "No encryption key provided. Using generated key. "
                "Set ENCRYPTION_KEY environment variable for persistent encryption."
            )

    def _derive_key(self, password: str) -> bytes:
        """Derive a Fernet-compatible key from a password using PBKDF2."""
        salt = b"bugbounty_automator_salt_v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string and return base64-encoded ciphertext."""
        if not plaintext:
            return plaintext

        if self._fernet is None:
            self._initialize()

        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt data")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext and return plaintext."""
        if not ciphertext:
            return ciphertext

        if self._fernet is None:
            self._initialize()

        try:
            encrypted = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """Encrypt specific fields in a dictionary."""
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(result[field])
        return result

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """Decrypt specific fields in a dictionary."""
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                try:
                    result[field] = self.decrypt(result[field])
                except ValueError:
                    logger.warning(f"Could not decrypt field {field}, leaving as-is")
        return result

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key suitable for Fernet."""
        return Fernet.generate_key().decode()

    def is_available(self) -> bool:
        """Check if encryption is properly initialized."""
        return self._fernet is not None


def get_encryption_service() -> EncryptionService:
    """Get the singleton encryption service instance."""
    return EncryptionService()
