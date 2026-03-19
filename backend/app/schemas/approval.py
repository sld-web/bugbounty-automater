"""Approval request schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.approval import ApprovalStatus, RiskLevel


class ApprovalRequestCreate(BaseModel):
    action_type: str = Field(..., min_length=1, max_length=100)
    action_description: str
    target_id: str
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: float = Field(default=50, ge=0, le=100)
    risk_factors: dict = Field(default_factory=dict)
    proposed_command: str | None = None
    plugin_name: str | None = None
    plugin_params: dict = Field(default_factory=dict)
    evidence: dict = Field(default_factory=dict)
    context: str | None = None
    timeout_minutes: int = Field(default=30, ge=1, le=1440)


class ApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approve|deny)$")
    decided_by: str = "system"
    modified_params: dict | None = None
    reason: str | None = None


class ApprovalRequestResponse(BaseModel):
    id: str
    action_type: str
    action_description: str
    status: ApprovalStatus
    target_id: str
    risk_level: RiskLevel
    risk_score: float
    risk_factors: dict
    proposed_command: str | None
    plugin_name: str | None
    plugin_params: dict
    evidence: dict
    context: str | None
    decided_by: str | None
    decided_at: datetime | None
    decision_reason: str | None
    modified_params: dict | None
    timeout_minutes: int
    expires_at: datetime | None
    notified_at: datetime | None
    notification_channel: str | None
    created_at: datetime
    updated_at: datetime
    target_name: str | None = None

    model_config = {"from_attributes": True}


class ApprovalListResponse(BaseModel):
    items: list[ApprovalRequestResponse]
    total: int
    pending_count: int


class ApprovalQueueResponse(BaseModel):
    pending: list[ApprovalRequestResponse]
    recent: list[ApprovalRequestResponse]
    stats: dict
