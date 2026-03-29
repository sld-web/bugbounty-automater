"""Learning metrics model for adaptive tuning and skill progression."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.target import Target


class LearningMetric(BaseModel):
    """Tracks success rates of hypothesis types per target for adaptive tuning."""
    __tablename__ = "learning_metrics"

    target_id: Mapped[str] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hypothesis_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    # Optional: notes or context about why this hypothesis type works/doesn't work
    context_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="learning_metrics")

    def update_rate(self) -> None:
        """Update success rate based on counts."""
        if self.attempt_count > 0:
            self.success_rate = self.success_count / self.attempt_count
        else:
            self.success_rate = 0.0
        self.last_updated = datetime.utcnow()

    def record_success(self) -> None:
        """Record a successful hypothesis test."""
        self.success_count += 1
        self.attempt_count += 1
        self.update_rate()

    def record_failure(self) -> None:
        """Record a failed hypothesis test."""
        self.attempt_count += 1
        self.update_rate()