"""Reporting API endpoints."""
from datetime import datetime
from typing import Annotated, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.finding import Finding as FindingModel
from app.services.report_generator import get_report_generator
from app.services.hackerone_api import HackerOneAPI
from app.services.bugcrowd_api import BugcrowdAPI

router = APIRouter(prefix="/reports", tags=["reporting"])


class Finding(BaseModel):
    title: str
    severity: str
    description: str
    impact: str
    steps_to_reproduce: list[str]
    cvss_vector: Optional[str] = None
    cvss_score: Optional[float] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    remediation: Optional[str] = None
    screenshots: list[str] = []


class ReportGenerateRequest(BaseModel):
    program_name: str
    target: str
    findings: list[Finding]
    format: str = "html"
    include_cvss: bool = True
    include_screenshots: bool = True
    include_remediation: bool = True


class ReportSubmitRequest(BaseModel):
    program_name: str
    target: str
    findings: list[Finding]
    platform: str
    hackerone_api_key: Optional[str] = None
    bugcrowd_api_key: Optional[str] = None


@router.post("/generate")
async def generate_report(request: ReportGenerateRequest) -> dict:
    """Generate a vulnerability report."""
    generator = get_report_generator()
    import uuid

    findings_data = [f.model_dump() for f in request.findings]
    report_id = str(uuid.uuid4())

    report_data = {
        "id": report_id,
        "program_name": request.program_name,
        "target": request.target,
        "findings": findings_data,
        "include_cvss": request.include_cvss,
        "include_screenshots": request.include_screenshots,
        "include_remediation": request.include_remediation,
    }

    if request.format == "html":
        content = generator.generate_html(
            program_name=request.program_name,
            target=request.target,
            findings=findings_data,
            cvss_scores=request.include_cvss,
            screenshots=request.include_screenshots,
            remediation=request.include_remediation,
        )
        report_data["html_content"] = content
    elif request.format == "markdown":
        content = generator.generate_markdown(
            program_name=request.program_name,
            target=request.target,
            findings=findings_data,
            cvss_scores=request.include_cvss,
            remediation=request.include_remediation,
        )
        report_data["html_content"] = content
    elif request.format == "pdf":
        import base64
        content = generator.generate_pdf(
            program_name=request.program_name,
            target=request.target,
            findings=findings_data,
            cvss_scores=request.include_cvss,
            remediation=request.include_remediation,
        )
        report_data["html_content"] = base64.b64encode(content).decode("utf-8") if isinstance(content, bytes) else content
        generator.save_report(report_id, report_data)
        return {
            "report_id": report_id,
            "format": "pdf",
            "content": report_data["html_content"],
            "filename": f"report_{request.program_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        }
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

    generator.save_report(report_id, report_data)

    return {
        "report_id": report_id,
        "format": request.format,
        "content": report_data["html_content"],
        "filename": f"report_{request.program_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}",
    }


@router.post("/save")
async def save_report(
    request: ReportGenerateRequest,
    path: str = Query(..., description="Output file path"),
) -> dict:
    """Generate and save a report to file."""
    generator = get_report_generator()

    findings_data = [f.model_dump() for f in request.findings]

    if request.format == "html":
        content = generator.generate_html(
            program_name=request.program_name,
            target=request.target,
            findings=findings_data,
            cvss_scores=request.include_cvss,
            screenshots=request.include_screenshots,
            remediation=request.include_remediation,
        )
        success = await generator.save_html(content, path)
    elif request.format == "markdown":
        content = generator.generate_markdown(
            program_name=request.program_name,
            target=request.target,
            findings=findings_data,
            cvss_scores=request.include_cvss,
            remediation=request.include_remediation,
        )
        success = await generator.save_markdown(content, path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

    if success:
        return {"message": "Report saved successfully", "path": path}
    raise HTTPException(status_code=500, detail="Failed to save report")


@router.post("/submit/hackerone")
async def submit_to_hackerone(request: ReportSubmitRequest) -> dict:
    """Submit a report to HackerOne."""
    if not request.hackerone_api_key:
        raise HTTPException(status_code=400, detail="HackerOne API key required")

    api = HackerOneAPI(request.hackerone_api_key)

    results = []
    for finding in request.findings:
        result = await api.create_report(
            program_id=request.program_name,
            title=finding.title,
            description=finding.description,
            severity=finding.severity,
            weakness=finding.cwe_id or "Other",
            impact=finding.impact,
            remediation=finding.remediation or "",
            cvss_vector=finding.cvss_vector,
        )
        results.append({
            "finding": finding.title,
            "result": result,
        })

    await api.close()

    success_count = sum(1 for r in results if r["result"].get("success"))
    return {
        "submitted": success_count,
        "total": len(request.findings),
        "results": results,
    }


@router.post("/submit/bugcrowd")
async def submit_to_bugcrowd(request: ReportSubmitRequest) -> dict:
    """Submit a report to Bugcrowd."""
    if not request.bugcrowd_api_key:
        raise HTTPException(status_code=400, detail="Bugcrowd API key required")

    api = BugcrowdAPI(request.bugcrowd_api_key)

    results = []
    for finding in request.findings:
        result = await api.create_submission(
            program_handle=request.program_name,
            title=finding.title,
            description=finding.description,
            severity=finding.severity,
            impact=finding.impact,
            steps_to_reproduce="\n".join(finding.steps_to_reproduce),
            remediation=finding.remediation,
            cvss_score=finding.cvss_score,
        )
        results.append({
            "finding": finding.title,
            "result": result,
        })

    await api.close()

    success_count = sum(1 for r in results if r["result"].get("success"))
    return {
        "submitted": success_count,
        "total": len(request.findings),
        "results": results,
    }


@router.get("/templates/{platform}")
async def get_report_template(platform: str) -> dict:
    """Get report template for a platform."""
    if platform == "hackerone":
        return {
            "platform": "hackerone",
            "fields": [
                {"name": "title", "required": True, "max_length": 150},
                {"name": "description", "required": True},
                {"name": "severity", "required": True, "options": ["critical", "high", "medium", "low", "informational"]},
                {"name": "weakness", "required": False},
                {"name": "impact", "required": True},
                {"name": "cvss_vector", "required": False},
                {"name": "steps_to_reproduce", "required": True},
                {"name": "remediation", "required": False},
            ],
        }
    elif platform == "bugcrowd":
        return {
            "platform": "bugcrowd",
            "fields": [
                {"name": "title", "required": True},
                {"name": "description", "required": True},
                {"name": "severity", "required": True, "options": ["P1", "P2", "P3", "P4", "P5"]},
                {"name": "impact", "required": True},
                {"name": "steps_to_reproduce", "required": True},
                {"name": "remediation_advice", "required": False},
                {"name": "cvss_score", "required": False},
            ],
        }
    else:
        raise HTTPException(status_code=404, detail="Platform not supported")


@router.post("/validate")
async def validate_report(request: ReportGenerateRequest) -> dict:
    """Validate a report before submission."""
    errors = []

    if not request.findings:
        errors.append("Report must contain at least one finding")

    for i, finding in enumerate(request.findings, 1):
        if not finding.title:
            errors.append(f"Finding {i}: title is required")
        if not finding.description:
            errors.append(f"Finding {i}: description is required")
        if not finding.impact:
            errors.append(f"Finding {i}: impact is required")
        if not finding.steps_to_reproduce:
            errors.append(f"Finding {i}: at least one step to reproduce is required")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


class AISummarizeRequest(BaseModel):
    target_id: str
    program_name: str = "Bug Bounty Program"
    findings: list[dict] | None = None


class AISummarizeResponse(BaseModel):
    summary: str
    ai_used: bool
    cached: bool = False


@router.post("/summarize", response_model=AISummarizeResponse)
async def generate_ai_summary(
    request: AISummarizeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate executive summary using AI."""
    from app.services.openai_service import openai_service
    
    if not openai_service.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available",
        )
    
    if request.findings:
        findings = request.findings
    else:
        result = await db.execute(
            select(FindingModel).where(FindingModel.target_id == request.target_id)
        )
        findings_db = result.scalars().all()
        findings = [
            {
                "id": f.id,
                "title": f.title,
                "description": f.description,
                "severity": f.severity.value if f.severity else "unknown",
                "vuln_type": f.vuln_type,
                "impact": f.impact,
            }
            for f in findings_db
        ]
    
    if not findings:
        return AISummarizeResponse(
            summary="No findings to summarize.",
            ai_used=False,
            cached=False,
        )
    
    summary = await openai_service.generate_report_summary(
        findings=findings,
        program_name=request.program_name,
    )
    
    return AISummarizeResponse(
        summary=summary,
        ai_used=True,
        cached=False,
    )


@router.get("/ai/status")
async def get_ai_status():
    """Get AI service status."""
    from app.services.openai_service import openai_service
    
    return {
        "available": openai_service.is_available,
        "model": openai_service.model if openai_service.is_available else None,
        "cache_stats": openai_service.get_cache_stats(),
    }


@router.get("/export/{report_id}")
async def export_report(
    report_id: str,
    format: str = Query("html", description="Export format: html, markdown, pdf"),
):
    """Export a generated report."""
    from app.services.report_generator import get_report_generator
    
    generator = get_report_generator()
    
    report = generator.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if format == "html":
        return {
            "format": "html",
            "content": report.get("html_content", ""),
            "content_type": "text/html",
        }
    elif format == "markdown":
        markdown_content = generator.generate_markdown(
            program_name=report.get("program_name", "Report"),
            target=report.get("target", ""),
            findings=report.get("findings", []),
        )
        return {
            "format": "markdown",
            "content": markdown_content,
            "content_type": "text/markdown",
        }
    elif format == "pdf":
        import base64
        pdf_content = generator.generate_pdf(
            program_name=report.get("program_name", "Report"),
            target=report.get("target", ""),
            findings=report.get("findings", []),
        )
        return {
            "format": "pdf",
            "content": base64.b64encode(pdf_content).decode("utf-8") if isinstance(pdf_content, bytes) else pdf_content,
            "content_type": "application/pdf",
        }
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


@router.get("/summary/{target_id}")
async def get_report_summary(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get summary statistics for a target's findings."""
    result = await db.execute(
        select(FindingModel).where(FindingModel.target_id == target_id)
    )
    findings = result.scalars().all()
    
    if not findings:
        return {
            "target_id": target_id,
            "total": 0,
            "findings": [],
            "severity_summary": {},
        }
    
    findings_data = [
        {
            "id": f.id,
            "title": f.title,
            "severity": f.severity.value if f.severity else "unknown",
            "vuln_type": f.vuln_type,
            "status": f.status.value if f.status else "unknown",
            "cvss_score": f.cvss_score,
        }
        for f in findings
    ]
    
    severity_counts = {}
    for f in findings_data:
        sev = f["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    return {
        "target_id": target_id,
        "total": len(findings),
        "findings": findings_data,
        "severity_summary": severity_counts,
    }
