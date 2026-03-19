"""PluginRun model for tracking plugin executions."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.target import Target


class PluginStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class PermissionLevel(str, Enum):
    SAFE = "SAFE"
    LIMITED = "LIMITED"
    DANGEROUS = "DANGEROUS"


class PluginRun(BaseModel):
    __tablename__ = "plugin_runs"

    plugin_name: Mapped[str] = mapped_column(String(100), nullable=False)
    plugin_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    status: Mapped[PluginStatus] = mapped_column(
        SQLEnum(PluginStatus),
        default=PluginStatus.QUEUED
    )
    
    target_id: Mapped[str] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Execution details
    permission_level: Mapped[PermissionLevel] = mapped_column(
        SQLEnum(PermissionLevel),
        default=PermissionLevel.SAFE
    )
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Container info
    container_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    container_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Timing
    queued_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Output
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Resource usage
    memory_used_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpu_seconds: Mapped[float | None] = mapped_column(Integer, nullable=True)
    
    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="plugin_runs")

    def mark_running(self) -> None:
        self.status = PluginStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, exit_code: int = 0, results: dict | None = None) -> None:
        self.status = PluginStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.exit_code = exit_code
        if self.started_at:
            self.duration_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )
        if results:
            self.results = results

    def mark_failed(self, error_message: str, exit_code: int | None = None) -> None:
        self.status = PluginStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.exit_code = exit_code
        if self.started_at:
            self.duration_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )

    def mark_timeout(self) -> None:
        self.status = PluginStatus.TIMED_OUT
        self.completed_at = datetime.utcnow()
        self.error_message = "Execution timed out"
