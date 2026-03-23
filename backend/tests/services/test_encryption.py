"""Tests for encryption service."""
import pytest
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Tests for encryption service."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        service = EncryptionService()
        plaintext = "my-secret-api-key-12345"
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert encrypted != plaintext
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """Test that empty strings are handled."""
        service = EncryptionService()
        
        assert service.encrypt("") == ""
        assert service.decrypt("") == ""

    def test_encrypt_none_returns_none(self):
        """Test that None input returns None."""
        service = EncryptionService()
        
        assert service.encrypt(None) is None
        assert service.decrypt(None) is None

    def test_different_plaintexts_produce_different_ciphertexts(self):
        """Test that different plaintexts produce different ciphertexts."""
        service = EncryptionService()
        
        enc1 = service.encrypt("key1")
        enc2 = service.encrypt("key2")
        
        assert enc1 != enc2

    def test_same_plaintext_produces_different_ciphertexts(self):
        """Test that encrypting same text twice produces different ciphertexts (due to IV)."""
        service = EncryptionService()
        
        enc1 = service.encrypt("same-key")
        enc2 = service.encrypt("same-key")
        
        assert enc1 != enc2
        assert service.decrypt(enc1) == "same-key"
        assert service.decrypt(enc2) == "same-key"

    def test_encrypt_dict(self):
        """Test encrypting specific fields in a dict."""
        service = EncryptionService()
        
        data = {"username": "user", "password": "secret", "api_key": "key123"}
        encrypted = service.encrypt_dict(data, ["password", "api_key"])
        
        assert encrypted["username"] == "user"
        assert encrypted["password"] != "secret"
        assert encrypted["api_key"] != "key123"
        
        decrypted = service.decrypt_dict(encrypted, ["password", "api_key"])
        assert decrypted["username"] == "user"
        assert decrypted["password"] == "secret"
        assert decrypted["api_key"] == "key123"

    def test_generate_key(self):
        """Test key generation."""
        key = EncryptionService.generate_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_is_available(self):
        """Test availability check."""
        service = EncryptionService()
        assert service.is_available() is True

    def test_decrypt_invalid_data(self):
        """Test that invalid ciphertext raises error."""
        service = EncryptionService()
        
        with pytest.raises(ValueError):
            service.decrypt("invalid-ciphertext")
