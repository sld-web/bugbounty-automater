"""Target model for individual testing targets."""
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.program import Program
    from app.models.finding import Finding
    from app.models.flow_card import FlowCard
    from app.models.plugin_run import PluginRun
    from app.models.approval import ApprovalRequest


class TargetStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TargetType(str, Enum):
    DOMAIN = "DOMAIN"
    IP = "IP"
    URL = "URL"
    MOBILE_APP = "MOBILE_APP"
    REPOSITORY = "REPOSITORY"


class Target(BaseModel):
    __tablename__ = "targets"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    target_type: Mapped[TargetType] = mapped_column(
        SQLEnum(TargetType),
        default=TargetType.DOMAIN
    )
    status: Mapped[TargetStatus] = mapped_column(
        SQLEnum(TargetStatus),
        default=TargetStatus.PENDING
    )
    
    program_id: Mapped[str] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Discovered data
    technologies: Mapped[list] = mapped_column(JSON, default=list)
    ports: Mapped[list] = mapped_column(JSON, default=list)
    subdomains: Mapped[list] = mapped_column(JSON, default=list)
    endpoints: Mapped[list] = mapped_column(JSON, default=list)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Coverage tracking
    surface_coverage: Mapped[int] = mapped_column(Integer, default=0)
    attack_vector_coverage: Mapped[int] = mapped_column(Integer, default=0)
    logic_flow_coverage: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    program: Mapped["Program"] = relationship("Program", back_populates="targets")
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="target",
        cascade="all, delete-orphan"
    )
    flow_cards: Mapped[list["FlowCard"]] = relationship(
        "FlowCard",
        back_populates="target",
        cascade="all, delete-orphan"
    )
    plugin_runs: Mapped[list["PluginRun"]] = relationship(
        "PluginRun",
        back_populates="target",
        cascade="all, delete-orphan"
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="target",
        cascade="all, delete-orphan"
    )

    def update_coverage(self) -> None:
        """Recalculate coverage percentages."""
        total_assets = len(self.subdomains) + len(self.endpoints)
        if total_assets > 0:
            tested = len([e for e in self.endpoints if e.get("tested")])
            self.surface_coverage = int((tested / total_assets) * 100)
