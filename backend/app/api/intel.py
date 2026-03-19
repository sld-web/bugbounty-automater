"""Intel API endpoints for intelligence layer."""
from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel

from app.models.finding import Finding, Severity

router = APIRouter(prefix="/intel", tags=["intelligence"])


class IntelFinding(BaseModel):
    source: str
    finding_type: str
    title: str
    description: str
    severity: Severity
    target_id: str | None = None
    target_pattern: str | None = None
    cve_id: str | None = None
    cwe_id: str | None = None
    evidence: dict | None = None
    public_refs: list[str] | None = None


@router.post("/findings")
async def submit_intel_finding(
    finding: IntelFinding,
    background_tasks: BackgroundTasks,
):
    """Submit a potential finding from intelligence sources."""
    background_tasks.add_task(process_intel_finding, finding)
    return {"status": "queued", "message": "Finding queued for processing"}


async def process_intel_finding(finding: IntelFinding):
    """Process an intelligence finding."""
    from app.database import get_db_context

    async with get_db_context() as db:
        finding_obj = Finding(
            title=finding.title,
            description=finding.description,
            severity=finding.severity,
            target_id=finding.target_id or "",
            vuln_type=finding.finding_type,
            cve_id=finding.cve_id,
            cwe_id=finding.cwe_id,
            evidence=finding.evidence or {},
            public_refs=finding.public_refs or [],
        )

        db.add(finding_obj)
        await db.commit()


@router.get("/sources")
async def list_intel_sources():
    """List configured intelligence sources."""
    return {
        "sources": [
            {
                "name": "NVD CVE Feed",
                "enabled": True,
                "type": "cve",
                "last_poll": None,
            },
            {
                "name": "GitHub Monitor",
                "enabled": True,
                "type": "github",
                "last_poll": None,
            },
            {
                "name": "AlienVault OTX",
                "enabled": True,
                "type": "otx",
                "last_poll": None,
            },
            {
                "name": "Shodan",
                "enabled": True,
                "type": "shodan",
                "last_poll": None,
            },
        ]
    }
