"""Coverage API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.coverage_tracker import CoverageTracker
from app.models.target import Target
from app.models.flow_card import FlowCard
from app.schemas.flow import CoverageResponse

router = APIRouter(prefix="/coverage", tags=["coverage"])


@router.get("/{target_id}", response_model=CoverageResponse)
async def get_coverage(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get coverage metrics for a target."""
    result = await db.execute(
        select(Target).where(Target.id == target_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    result = await db.execute(
        select(FlowCard).where(FlowCard.target_id == target_id)
    )
    flow_cards = result.scalars().all()

    target_data = {
        "id": target.id,
        "subdomains": target.subdomains,
        "endpoints": target.endpoints,
        "technologies": target.technologies,
    }

    cards_data = [
        {
            "card_type": c.card_type.value,
            "name": c.name,
            "status": c.status.value,
        }
        for c in flow_cards
    ]

    tracker = CoverageTracker()
    return tracker.get_coverage(target_data, cards_data)


@router.get("/{target_id}/missing")
async def get_missing_coverage(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get areas with missing coverage."""
    result = await db.execute(
        select(Target).where(Target.id == target_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    result = await db.execute(
        select(FlowCard).where(FlowCard.target_id == target_id)
    )
    flow_cards = result.scalars().all()

    target_data = {
        "id": target.id,
        "subdomains": target.subdomains,
        "endpoints": target.endpoints,
        "technologies": target.technologies,
    }

    cards_data = [
        {
            "card_type": c.card_type.value,
            "name": c.name,
            "status": c.status.value,
        }
        for c in flow_cards
    ]

    vuln_types = [
        "sql_injection",
        "xss",
        "csrf",
        "ssrf",
        "open_redirect",
        "idor",
        "rce",
        "lfi",
        "rfi",
        "xxe",
    ]

    tracker = CoverageTracker()
    return tracker.get_missing_coverage(target_data, cards_data, vuln_types)
