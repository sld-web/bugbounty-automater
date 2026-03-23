"""Finding API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.finding import Finding, Severity, FindingStatus
from app.schemas.finding import (
    FindingCreate,
    FindingUpdate,
    FindingResponse,
    FindingListResponse,
)

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("", response_model=FindingListResponse)
async def list_findings(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    target_id: str | None = None,
    severity: Severity | None = None,
    finding_status: FindingStatus | None = Query(default=None, alias="status"),
):
    """List all findings with optional filters."""
    query = select(Finding)
    count_query = select(func.count(Finding.id))

    if target_id:
        query = query.where(Finding.target_id == target_id)
        count_query = count_query.where(Finding.target_id == target_id)

    if severity:
        query = query.where(Finding.severity == severity)
        count_query = count_query.where(Finding.severity == severity)

    if finding_status:
        query = query.where(Finding.status == finding_status)
        count_query = count_query.where(Finding.status == finding_status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Finding.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    findings = result.scalars().all()

    return FindingListResponse(
        items=[FindingResponse.model_validate(f) for f in findings],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific finding by ID."""
    result = await db.execute(
        select(Finding).where(Finding.id == finding_id)
    )
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    return FindingResponse.model_validate(finding)


@router.post("", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
async def create_finding(
    finding_data: FindingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new finding."""
    finding = Finding(
        title=finding_data.title,
        description=finding_data.description,
        severity=finding_data.severity,
        target_id=finding_data.target_id,
        vuln_type=finding_data.vuln_type,
        affected_url=finding_data.affected_url,
        affected_parameter=finding_data.affected_parameter,
        cve_id=finding_data.cve_id,
        cwe_id=finding_data.cwe_id,
        evidence=finding_data.evidence,
        screenshots=finding_data.screenshots,
        request_response=finding_data.request_response,
        remediation=finding_data.remediation,
        impact=finding_data.impact,
        cvss_score=finding_data.cvss_score,
    )

    db.add(finding)
    await db.commit()
    await db.refresh(finding)

    return FindingResponse.model_validate(finding)


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str,
    finding_data: FindingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a finding."""
    result = await db.execute(
        select(Finding).where(Finding.id == finding_id)
    )
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    update_data = finding_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(finding, field, value)

    await db.commit()
    await db.refresh(finding)

    return FindingResponse.model_validate(finding)


@router.delete("/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(
    finding_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a finding."""
    result = await db.execute(
        select(Finding).where(Finding.id == finding_id)
    )
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    await db.delete(finding)
    await db.commit()


@router.get("/stats/summary")
async def get_finding_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get summary statistics for findings."""
    severity_query = select(
        Finding.severity,
        func.count(Finding.id).label("count")
    ).group_by(Finding.severity)

    status_query = select(
        Finding.status,
        func.count(Finding.id).label("count")
    ).group_by(Finding.status)

    severity_result = await db.execute(severity_query)
    status_result = await db.execute(status_query)

    by_severity = {s.value: 0 for s in Severity}
    for row in severity_result:
        by_severity[row.severity.value] = row.count

    by_status = {s.value: 0 for s in FindingStatus}
    for row in status_result:
        by_status[row.status.value] = row.count

    total_result = await db.execute(select(func.count(Finding.id)))
    total = total_result.scalar() or 0

    return {
        "total": total,
        "by_severity": by_severity,
        "by_status": by_status,
    }


class AIFindingsEnhanceRequest(BaseModel):
    target_id: str | None = None
    program_context: dict | None = None


class AIFindingsEnhanceResponse(BaseModel):
    finding_id: str
    enhanced: dict
    ai_used: bool


class AIClassifyRequest(BaseModel):
    description: str


class AIClassifyResponse(BaseModel):
    vulnerability_type: str
    severity: str
    confidence: float
    cwe_id: str | None = None
    cvss_vector: str | None = None
    ai_used: bool


@router.post("/{finding_id}/enhance", response_model=AIFindingsEnhanceResponse)
async def enhance_finding_with_ai(
    finding_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: AIFindingsEnhanceRequest | None = None,
):
    """Enhance a finding using AI."""
    from app.services.openai_service import openai_service
    
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    
    if not openai_service.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available",
        )
    
    finding_dict = {
        "title": finding.title,
        "description": finding.description,
        "vuln_type": finding.vuln_type,
        "affected_url": finding.affected_url,
        "cvss_score": finding.cvss_score,
    }
    
    program_context = request.program_context if request else {}
    
    enhanced = await openai_service.enhance_finding(finding_dict, program_context)
    
    return AIFindingsEnhanceResponse(
        finding_id=finding_id,
        enhanced=enhanced,
        ai_used=True,
    )


@router.post("/ai/classify", response_model=AIClassifyResponse)
async def classify_vulnerability(
    request: AIClassifyRequest,
):
    """Classify a vulnerability using AI."""
    from app.services.openai_service import openai_service
    
    if not openai_service.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available",
        )
    
    result = await openai_service.classify_vulnerability(request.description)
    
    return AIClassifyResponse(
        vulnerability_type=result.get("type", "unknown"),
        severity=result.get("severity", "unknown"),
        confidence=result.get("confidence", 0.0),
        cwe_id=result.get("cwe_id"),
        cvss_vector=result.get("cvss_vector"),
        ai_used=True,
    )


@router.get("/ai/cache/stats")
async def get_ai_cache_stats():
    """Get AI cache statistics."""
    from app.services.openai_service import openai_service
    
    return openai_service.get_cache_stats()


@router.post("/ai/cache/clear")
async def clear_ai_cache():
    """Clear AI cache."""
    from app.services.cache import openai_cache
    
    count = openai_cache.clear()
    return {"message": f"Cleared {count} cache entries"}


class BatchEnhanceRequest(BaseModel):
    ids: list[str]
    program_context: dict | None = None


class BatchEnhanceResponse(BaseModel):
    total: int
    enhanced: int
    failed: int
    results: list[dict]


@router.post("/batch-enhance", response_model=BatchEnhanceResponse)
async def batch_enhance_findings(
    request: BatchEnhanceRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Batch enhance multiple findings using AI."""
    from app.services.openai_service import openai_service
    
    if not openai_service.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available",
        )
    
    results = []
    enhanced_count = 0
    failed_count = 0
    
    for finding_id in request.ids:
        result = await db.execute(select(Finding).where(Finding.id == finding_id))
        finding = result.scalar_one_or_none()
        
        if not finding:
            results.append({"finding_id": finding_id, "status": "not_found"})
            failed_count += 1
            continue
        
        finding_dict = {
            "title": finding.title,
            "description": finding.description,
            "vuln_type": finding.vuln_type,
            "affected_url": finding.affected_url,
            "cvss_score": finding.cvss_score,
        }
        
        try:
            enhanced = await openai_service.enhance_finding(
                finding_dict, 
                request.program_context or {}
            )
            results.append({
                "finding_id": finding_id,
                "status": "enhanced",
                "enhanced": enhanced,
            })
            enhanced_count += 1
        except Exception as e:
            results.append({
                "finding_id": finding_id,
                "status": "failed",
                "error": str(e),
            })
            failed_count += 1
    
    return BatchEnhanceResponse(
        total=len(request.ids),
        enhanced=enhanced_count,
        failed=failed_count,
        results=results,
    )
