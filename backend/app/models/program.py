"""Program model for bug bounty program configurations."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.target import Target
    from app.models.credential import Credential


class Program(BaseModel):
    __tablename__ = "programs"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Configuration stored as JSON
    scope_domains: Mapped[list] = mapped_column(JSON, default=list)
    scope_excluded: Mapped[list] = mapped_column(JSON, default=list)
    scope_mobile_apps: Mapped[list] = mapped_column(JSON, default=list)
    scope_repositories: Mapped[list] = mapped_column(JSON, default=list)
    
    priority_areas: Mapped[list] = mapped_column(JSON, default=list)
    out_of_scope: Mapped[list] = mapped_column(JSON, default=list)
    severity_mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    reward_tiers: Mapped[dict] = mapped_column(JSON, default=dict)
    campaigns: Mapped[list] = mapped_column(JSON, default=list)
    special_requirements: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Detailed target configurations for workflow generation
    target_configs: Mapped[list] = mapped_column(JSON, default=list)
    workflow_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    credential_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Ingestion metadata
    raw_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Integer, default=0)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    targets: Mapped[list["Target"]] = relationship(
        "Target",
        back_populates="program",
        cascade="all, delete-orphan"
    )
    credentials: Mapped[list["Credential"]] = relationship(
        "Credential",
        back_populates="program",
        cascade="all, delete-orphan"
    )

    def is_in_scope(self, target: str) -> bool:
        """Check if a target is within the program scope."""
        import fnmatch
        import tldextract
        
        # Check excluded patterns first
        for pattern in self.scope_excluded:
            if fnmatch.fnmatch(target, pattern):
                return False
        
        # Check included patterns
        for pattern in self.scope_domains:
            if fnmatch.fnmatch(target, pattern):
                return True
        
        # Check if it's a subdomain of any in-scope domain
        extracted = tldextract.extract(target)
        domain = f"{extracted.domain}.{extracted.suffix}"
        
        for pattern in self.scope_domains:
            if "*." in pattern:
                base_domain = pattern.replace("*.", "")
                if domain.endswith(base_domain):
                    return True
            elif domain == pattern.replace("*.", ""):
                return True
        
        return False

    def get_auth_level(self) -> str:
        """Get authentication level requirement from credential policy."""
        policy = self.credential_policy or {}
        return policy.get("requirement_level", "optional")

    def get_allowed_email_domains(self) -> list[str]:
        """Get allowed email domains for credentials."""
        policy = self.credential_policy or {}
        return policy.get("allowed_domains", [])

    def get_custom_headers(self) -> dict[str, str]:
        """Get custom headers to inject with credentials."""
        policy = self.credential_policy or {}
        return policy.get("custom_headers", {})

    def requires_auth(self) -> bool:
        """Check if this program requires authentication."""
        level = self.get_auth_level()
        return level in ["required", "program_provided", "domain_validated"]

    def allows_public_testing(self) -> bool:
        """Check if public (non-authenticated) testing is allowed."""
        policy = self.credential_policy or {}
        return policy.get("public_testing_allowed", True)

    def get_provisioning_info(self) -> dict | None:
        """Get test account provisioning information if available."""
        policy = self.credential_policy or {}
        return policy.get("provisioning")

    def requires_program_account(self) -> bool:
        """Check if program-provided accounts are required."""
        return self.get_auth_level() == "program_provided"
