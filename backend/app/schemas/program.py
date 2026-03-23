"""Program schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class ScopeConfig(BaseModel):
    domains: list[str] = Field(default_factory=list)
    excluded: list[str] = Field(default_factory=list)
    mobile_apps: list[dict] = Field(default_factory=list)
    repositories: list[str] = Field(default_factory=list)


class CampaignConfig(BaseModel):
    name: str
    multiplier: float = 1.0
    applies_to: list[str] = Field(default_factory=list)
    end_date: str | None = None


class ProgramCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., pattern="^(hackerone|bugcrowd|yeswehack|openbugbounty|manual)$")
    url: str | None = None
    raw_policy: str | None = None
    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    priority_areas: list[str] = Field(default_factory=list)
    target_configs: list[dict] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    severity_mapping: dict = Field(default_factory=dict)
    reward_tiers: dict = Field(default_factory=dict)
    campaigns: list[CampaignConfig] = Field(default_factory=list)
    special_requirements: dict = Field(default_factory=dict)


class ProgramUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    scope: ScopeConfig | None = None
    priority_areas: list[str] | None = None
    target_configs: list[dict] | None = None
    out_of_scope: list[str] | None = None
    severity_mapping: dict | None = None
    reward_tiers: dict | None = None
    campaigns: list[CampaignConfig] | None = None
    special_requirements: dict | None = None
    reviewed: bool = False
    review_notes: str | None = None


class ProgramResponse(BaseModel):
    id: str
    name: str
    platform: str
    url: str | None
    scope: ScopeConfig
    scope_domains: list[str] = []
    scope_excluded: list[str] = []
    priority_areas: list[str]
    target_configs: list[dict] = []
    workflow_data: dict | None = None
    out_of_scope: list[str]
    severity_mapping: dict
    reward_tiers: dict
    campaigns: list[CampaignConfig]
    special_requirements: dict
    confidence_score: float
    needs_review: bool
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime
    updated_at: datetime
    target_count: int = 0
    finding_count: int = 0

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_extras(cls, program):
        """Create response with extra fields."""
        return cls(
            id=program.id,
            name=program.name,
            platform=program.platform,
            url=program.url,
            scope=ScopeConfig(
                domains=program.scope_domains or [],
                excluded=program.scope_excluded or [],
            ),
            scope_domains=program.scope_domains or [],
            scope_excluded=program.scope_excluded or [],
            priority_areas=program.priority_areas or [],
            target_configs=program.target_configs or [],
            workflow_data=program.workflow_data,
            out_of_scope=program.out_of_scope or [],
            severity_mapping=program.severity_mapping or {},
            reward_tiers=program.reward_tiers or {},
            campaigns=[],
            special_requirements=program.special_requirements or {},
            confidence_score=program.confidence_score or 0,
            needs_review=program.needs_review,
            reviewed_at=program.reviewed_at,
            review_notes=program.review_notes,
            created_at=program.created_at,
            updated_at=program.updated_at,
        )


class ProgramConfigResponse(BaseModel):
    program_id: str
    program_name: str
    scope: ScopeConfig
    priority_areas: list[str]
    out_of_scope: list[str]
    severity_mapping: dict
    reward_tiers: dict
    campaigns: list[CampaignConfig]
    special_requirements: dict
    confidence_score: float
