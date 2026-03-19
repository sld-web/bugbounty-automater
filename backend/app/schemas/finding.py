"""Finding schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.finding import FindingStatus, Severity


class FindingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str
    severity: Severity = Severity.UNKNOWN
    target_id: str
    vuln_type: str
    affected_url: str | None = None
    affected_parameter: str | None = None
    cve_id: str | None = None
    cwe_id: str | None = None
    evidence: dict = Field(default_factory=dict)
    screenshots: list = Field(default_factory=list)
    request_response: dict = Field(default_factory=dict)
    remediation: str | None = None
    impact: str | None = None
    cvss_score: float | None = None


class FindingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: Severity | None = None
    status: FindingStatus | None = None
    evidence: dict | None = None
    remediation: str | None = None
    impact: str | None = None
    cvss_score: float | None = None
    public_refs: list | None = None
    internal_refs: list | None = None
    report_id: str | None = None
    report_url: str | None = None


class FindingResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: Severity
    status: FindingStatus
    target_id: str
    vuln_type: str
    affected_url: str | None
    affected_parameter: str | None
    cve_id: str | None
    cwe_id: str | None
    evidence: dict
    screenshots: list
    request_response: dict
    remediation: str | None
    impact: str | None
    cvss_score: float | None
    public_refs: list
    internal_refs: list
    report_id: str | None
    report_url: str | None
    reported_at: datetime | None
    created_at: datetime
    updated_at: datetime
    target_name: str | None = None

    model_config = {"from_attributes": True}


class FindingListResponse(BaseModel):
    items: list[FindingResponse]
    total: int
    page: int
    page_size: int
