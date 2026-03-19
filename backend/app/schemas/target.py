"""Target schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.target import TargetStatus, TargetType


class TargetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    target_type: TargetType = TargetType.DOMAIN
    program_id: str
    metadata: dict = Field(default_factory=dict)


class TargetUpdate(BaseModel):
    name: str | None = None
    status: TargetStatus | None = None
    technologies: list | None = None
    ports: list | None = None
    subdomains: list | None = None
    endpoints: list | None = None
    metadata: dict | None = None
    surface_coverage: int | None = None
    attack_vector_coverage: int | None = None
    logic_flow_coverage: int | None = None


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
    metadata: dict
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
