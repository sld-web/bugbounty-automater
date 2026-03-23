"""Coverage API endpoints."""
from typing import Annotated
from collections import Counter

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


@router.get("/{target_id}/dashboard")
async def get_coverage_dashboard(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get comprehensive coverage dashboard data."""
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

    status_counts = Counter(c.status.value for c in flow_cards)
    total = len(flow_cards)
    completed = status_counts.get("done", 0) + status_counts.get("completed", 0)

    category_map = {
        "recon": ["reconnaissance", "scanning"],
        "discovery": ["discovery", "enumeration"],
        "attack": ["attack", "exploitation"],
        "verification": ["verification", "validation"],
    }

    by_category = {}
    for cat, types in category_map.items():
        cat_cards = [
            {
                "id": str(c.id),
                "name": c.name,
                "status": c.status.value,
            }
            for c in flow_cards
            if any(t in c.name.lower() for t in types) or c.card_type.value in types
        ]
        cat_completed = sum(
            1 for card in cat_cards
            if card["status"] in ["done", "completed"]
        )
        by_category[cat] = {
            "name": cat.title(),
            "cards": cat_cards,
            "total": len(cat_cards),
            "completed": cat_completed,
            "coverage": int(cat_completed / len(cat_cards) * 100) if cat_cards else 0,
        }

    severity_breakdown = Counter(c.severity for c in flow_cards if c.severity)

    recommendations = []
    if completed < total * 0.5:
        recommendations.append({
            "type": "low_coverage",
            "message": "Coverage is below 50%. Consider running additional recon and attack plugins.",
            "priority": "high",
        })

    for cat, data in by_category.items():
        if data["coverage"] < 50:
            recommendations.append({
                "type": f"{cat}_incomplete",
                "message": f"{data['name']} phase coverage is low ({data['coverage']}%).",
                "priority": "medium",
            })

    return {
        "target_id": target_id,
        "target_name": target.name,
        "summary": {
            "total_flow_cards": total,
            "completed": completed,
            "in_progress": status_counts.get("running", 0) + status_counts.get("pending", 0),
            "pending": status_counts.get("pending", 0),
            "coverage_percentage": int(completed / total * 100) if total > 0 else 0,
        },
        "by_category": by_category,
        "severity_breakdown": {
            "critical": severity_breakdown.get("critical", 0),
            "high": severity_breakdown.get("high", 0),
            "medium": severity_breakdown.get("medium", 0),
            "low": severity_breakdown.get("low", 0),
            "informational": severity_breakdown.get("informational", 0),
        },
        "recommendations": recommendations,
    }
