"""ApprovalRequest model for human-in-the-loop decisions."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.target import Target


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalRequest(BaseModel):
    __tablename__ = "approval_requests"

    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[ApprovalStatus] = mapped_column(
        SQLEnum(ApprovalStatus),
        default=ApprovalStatus.PENDING
    )
    
    target_id: Mapped[str] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Risk assessment
    risk_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel),
        default=RiskLevel.MEDIUM
    )
    risk_score: Mapped[float] = mapped_column(Integer, default=50)
    risk_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Action details
    proposed_command: Mapped[str | None] = mapped_column(Text, nullable=True)
    plugin_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    plugin_params: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Evidence
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Decision
    decided_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    modified_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Timing
    timeout_minutes: Mapped[int] = mapped_column(Integer, default=30)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Notifications
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notification_channel: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="approval_requests")

    def approve(self, decided_by: str, modified_params: dict | None = None, reason: str | None = None) -> None:
        self.status = ApprovalStatus.APPROVED
        self.decided_by = decided_by
        self.decided_at = datetime.utcnow()
        self.decision_reason = reason
        self.modified_params = modified_params

    def deny(self, decided_by: str, reason: str) -> None:
        self.status = ApprovalStatus.DENIED
        self.decided_by = decided_by
        self.decided_at = datetime.utcnow()
        self.decision_reason = reason

    def timeout(self) -> None:
        self.status = ApprovalStatus.TIMED_OUT
        self.decided_at = datetime.utcnow()

    def is_expired(self) -> bool:
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False
