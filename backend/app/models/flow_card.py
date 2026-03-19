"""FlowCard model for tracking testing workflow."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.target import Target


class CardType(str, Enum):
    ASSET = "ASSET"
    FLOW = "FLOW"
    ATTACK = "ATTACK"
    FINDING = "FINDING"


class CardStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    REVIEW = "REVIEW"
    DONE = "DONE"
    FLAGGED = "FLAGGED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class FlowCard(BaseModel):
    __tablename__ = "flow_cards"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    card_type: Mapped[CardType] = mapped_column(
        SQLEnum(CardType),
        nullable=False
    )
    status: Mapped[CardStatus] = mapped_column(
        SQLEnum(CardStatus),
        default=CardStatus.NOT_STARTED
    )
    
    target_id: Mapped[str] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("flow_cards.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Card-specific data
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Position in flowchart
    position_x: Mapped[int] = mapped_column(Integer, default=0)
    position_y: Mapped[int] = mapped_column(Integer, default=0)
    
    # Results
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    logs: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="flow_cards")
    parent: Mapped["FlowCard | None"] = relationship(
        "FlowCard",
        remote_side="FlowCard.id",
        back_populates="children"
    )
    children: Mapped[list["FlowCard"]] = relationship(
        "FlowCard",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    def mark_running(self) -> None:
        self.status = CardStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_done(self, results: dict | None = None) -> None:
        self.status = CardStatus.DONE
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )
        if results:
            self.results = results

    def mark_failed(self, error: str) -> None:
        self.status = CardStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
