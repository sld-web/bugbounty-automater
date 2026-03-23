"""Credential model for storing sensitive credentials."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.program import Program


class CredentialType(str, Enum):
    USER_PASS = "user_pass"
    API_KEY = "api_key"
    SESSION_TOKEN = "session_token"
    CERTIFICATE = "certificate"
    TOTP = "totp"


class Credential(BaseModel):
    __tablename__ = "credentials"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credential_type: Mapped[CredentialType] = mapped_column(
        SQLEnum(CredentialType),
        nullable=False
    )
    
    program_id: Mapped[str | None] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=True
    )
    
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    _password: Mapped[str | None] = mapped_column("password", Text, nullable=True)
    _api_key: Mapped[str | None] = mapped_column("api_key", Text, nullable=True)
    _token: Mapped[str | None] = mapped_column("token", Text, nullable=True)
    
    encrypted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    use_count: Mapped[int] = mapped_column(default=0)
    
    program: Mapped["Program | None"] = relationship("Program", back_populates="credentials")

    _encryption_service = None

    @classmethod
    def _get_encryption_service(cls):
        """Lazy load encryption service to avoid circular imports."""
        if cls._encryption_service is None:
            try:
                from app.services.encryption_service import get_encryption_service
                cls._encryption_service = get_encryption_service()
            except ImportError:
                cls._encryption_service = None
        return cls._encryption_service

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def password(self) -> str | None:
        return self.get_decrypted_password()

    @password.setter
    def password(self, value: str | None) -> None:
        if value is None:
            self._password = None
            return
        
        enc = self._get_encryption_service()
        if enc and enc.is_available():
            try:
                self._password = enc.encrypt(value)
            except Exception:
                self._password = value
        else:
            self._password = value

    @property
    def api_key(self) -> str | None:
        return self.get_decrypted_api_key()

    @api_key.setter
    def api_key(self, value: str | None) -> None:
        if value is None:
            self._api_key = None
            return
        
        enc = self._get_encryption_service()
        if enc and enc.is_available():
            try:
                self._api_key = enc.encrypt(value)
            except Exception:
                self._api_key = value
        else:
            self._api_key = value

    @property
    def token(self) -> str | None:
        return self.get_decrypted_token()

    @token.setter
    def token(self, value: str | None) -> None:
        if value is None:
            self._token = None
            return
        
        enc = self._get_encryption_service()
        if enc and enc.is_available():
            try:
                self._token = enc.encrypt(value)
            except Exception:
                self._token = value
        else:
            self._token = value

    def get_decrypted_password(self) -> Optional[str]:
        """Get decrypted password."""
        if not self._password:
            return None
        enc = self._get_encryption_service()
        if enc and enc.is_available():
            try:
                return enc.decrypt(self._password)
            except Exception:
                return self._password
        return self._password

    def get_decrypted_api_key(self) -> Optional[str]:
        """Get decrypted API key."""
        if not self._api_key:
            return None
        enc = self._get_encryption_service()
        if enc and enc.is_available():
            try:
                return enc.decrypt(self._api_key)
            except Exception:
                return self._api_key
        return self._api_key

    def get_decrypted_token(self) -> Optional[str]:
        """Get decrypted token."""
        if not self._token:
            return None
        enc = self._get_encryption_service()
        if enc and enc.is_available():
            try:
                return enc.decrypt(self._token)
            except Exception:
                return self._token
        return self._token

    def to_dict(self, include_secrets: bool = False) -> dict:
        """Convert to dictionary, optionally including decrypted secrets."""
        result = {
            "id": self.id,
            "name": self.name,
            "credential_type": self.credential_type.value if self.credential_type else None,
            "program_id": self.program_id,
            "username": self.username,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "use_count": self.use_count,
            "extra_data": self.extra_data,
        }
        
        if include_secrets:
            result["password"] = self.get_decrypted_password()
            result["api_key"] = self.get_decrypted_api_key()
            result["token"] = self.get_decrypted_token()
        else:
            result["has_password"] = bool(self._password)
            result["has_api_key"] = bool(self._api_key)
            result["has_token"] = bool(self._token)
        
        return result
