"""Finding model for discovered vulnerabilities."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.target import Target


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    UNKNOWN = "UNKNOWN"


class FindingStatus(str, Enum):
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    DUPLICATE = "DUPLICATE"
    RESOLVED = "RESOLVED"
    WORTHLESS = "WORTHLESS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Finding(BaseModel):
    __tablename__ = "findings"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(
        SQLEnum(Severity),
        default=Severity.UNKNOWN
    )
    status: Mapped[FindingStatus] = mapped_column(
        SQLEnum(FindingStatus),
        default=FindingStatus.NEW
    )
    
    target_id: Mapped[str] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Vulnerability details
    vuln_type: Mapped[str] = mapped_column(String(100), nullable=False)
    affected_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    affected_parameter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cve_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cwe_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Evidence
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    screenshots: Mapped[list] = mapped_column(JSON, default=list)
    request_response: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Remediation
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Tracking
    cvss_score: Mapped[float | None] = mapped_column(Integer, nullable=True)
    public_refs: Mapped[list] = mapped_column(JSON, default=list)
    internal_refs: Mapped[list] = mapped_column(JSON, default=list)
    
    # Report tracking
    report_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    report_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="findings")

    def calculate_severity_from_mapping(self, severity_mapping: dict) -> Severity:
        """Calculate severity based on program-specific mapping."""
        for level, vuln_types in severity_mapping.items():
            if self.vuln_type in vuln_types:
                return Severity(level.upper())
        return Severity.UNKNOWN
