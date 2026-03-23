"""Credential schemas for API validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.credential import CredentialType


class CredentialBase(BaseModel):
    name: str = Field(..., description="Human-readable credential name")
    credential_type: CredentialType = Field(..., description="Type of credential")
    username: Optional[str] = Field(None, description="Username for user_pass type")
    password: Optional[str] = Field(None, description="Password for user_pass type")
    api_key: Optional[str] = Field(None, description="API key for api_key type")
    token: Optional[str] = Field(None, description="Token for session_token type")
    expires_at: Optional[datetime] = Field(None, description="Expiration datetime")
    is_active: bool = Field(True, description="Whether credential is active")
    program_id: Optional[str] = Field(None, description="Associated program ID")


class CredentialCreate(CredentialBase):
    pass


class CredentialUpdate(BaseModel):
    name: Optional[str] = None
    credential_type: Optional[CredentialType] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class CredentialResponse(CredentialBase):
    id: str
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    is_expired: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CredentialListResponse(BaseModel):
    items: list[CredentialResponse]
    total: int
    page: int = 1
    page_size: int = 100
