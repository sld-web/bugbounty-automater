"""Target schemas."""
import html
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.target import TargetStatus, TargetType


def sanitize_input(value: str) -> str:
    """Sanitize input to prevent XSS attacks."""
    if not value:
        return value
    escaped = html.escape(value, quote=True)
    escaped = escaped.replace('\n', '').replace('\r', '').replace('\t', '')
    script_pattern = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
    escaped = script_pattern.sub('', escaped)
    event_pattern = re.compile(r'\bon\w+\s*=', re.IGNORECASE)
    escaped = event_pattern.sub('', escaped)
    return escaped.strip()


class TargetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    target_type: TargetType = TargetType.DOMAIN
    program_id: str
    target_metadata: dict = Field(default_factory=dict)

    @field_validator('name', mode='before')
    @classmethod
    def sanitize_name(cls, v):
        if isinstance(v, str):
            return sanitize_input(v)
        return v


class TargetUpdate(BaseModel):
    name: str | None = None
    status: TargetStatus | None = None
    technologies: list | None = None
    ports: list | None = None
    subdomains: list | None = None
    endpoints: list | None = None
    target_metadata: dict | None = None
    surface_coverage: int | None = None
    attack_vector_coverage: int | None = None
    logic_flow_coverage: int | None = None

    @field_validator('name', mode='before')
    @classmethod
    def sanitize_name(cls, v):
        if isinstance(v, str):
            return sanitize_input(v)
        return v


class TargetResponse(BaseModel):
    id: str
    name: str
    target_type: TargetType
    status: TargetStatus
    program_id: str
    technologies: list
    ports: list
    subdomains: list
    endpoints: list
    endpoint_classifications: dict
    target_metadata: dict
    surface_coverage: int
    attack_vector_coverage: int
    logic_flow_coverage: int
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime
    program_name: str | None = None

    model_config = {"from_attributes": True}


class TargetStatusResponse(BaseModel):
    id: str
    status: TargetStatus
    error_message: str | None
    retry_count: int
    surface_coverage: int
    attack_vector_coverage: int
    logic_flow_coverage: int


class TargetListResponse(BaseModel):
    items: list[TargetResponse]
    total: int
    page: int
    page_size: int
