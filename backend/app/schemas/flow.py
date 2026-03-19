"""Flow card schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.flow_card import CardStatus, CardType


class FlowCardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    card_type: CardType
    target_id: str
    parent_id: str | None = None
    description: str | None = None
    card_metadata: dict = Field(default_factory=dict)
    position_x: int = 0
    position_y: int = 0


class FlowCardUpdate(BaseModel):
    name: str | None = None
    status: CardStatus | None = None
    description: str | None = None
    card_metadata: dict | None = None
    position_x: int | None = None
    position_y: int | None = None
    results: dict | None = None
    logs: list | None = None
    error: str | None = None


class FlowCardResponse(BaseModel):
    id: str
    name: str
    card_type: CardType
    status: CardStatus
    target_id: str
    parent_id: str | None
    description: str | None
    card_metadata: dict
    position_x: int
    position_y: int
    results: dict
    logs: list
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FlowDAGResponse(BaseModel):
    target_id: str
    cards: list[FlowCardResponse]
    edges: list[dict]
    stats: dict


class CoverageResponse(BaseModel):
    target_id: str
    surface_coverage: int
    attack_vector_coverage: int
    logic_flow_coverage: int
    total_assets: int
    tested_assets: int
    total_attack_vectors: int
    attempted_attack_vectors: int
    total_flows: int
    tested_flows: int
