"""API endpoints for hypothesis generation with adaptive tuning."""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.target import Target
from app.services.adaptive_tuning.service import adaptive_tuning_service

router = APIRouter()


class HypothesisResponse(BaseModel):
    id: str
    description: str
    type: str
    endpoint: str
    method: str
    payload: str
    expected_behavior: str
    adaptive_weight: float
    is_blind_spot: bool
    is_recommended: bool
    priority_score: float


class HypothesesResponse(BaseModel):
    target_id: str
    hypotheses: List[HypothesisResponse]
    adaptive_weights: dict
    blind_spots: list
    recommended_types: list
    total_hypotheses: int


@router.get("/target/{target_id}", response_model=HypothesesResponse)
async def get_target_hypotheses(
    target_id: str = Path(..., description="The target ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get hypotheses for a target with adaptive tuning weights."""
    # Get the target
    from sqlalchemy import select

    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Get hypotheses with adaptive tuning
    result_data = await adaptive_tuning_service.integrate_with_hypothesis_generation(
        target, db
    )

    # Convert to response format
    hypotheses = []
    for hyp in result_data["hypotheses"]:
        hypotheses.append(
            HypothesisResponse(
                id=hyp["id"],
                description=hyp["description"],
                type=hyp["type"],
                endpoint=hyp["endpoint"],
                method=hyp["method"],
                payload=hyp["payload"],
                expected_behavior=hyp["expected_behavior"],
                adaptive_weight=hyp["adaptive_weight"],
                is_blind_spot=hyp["is_blind_spot"],
                is_recommended=hyp["is_recommended"],
                priority_score=hyp["priority_score"],
            )
        )

    return HypothesesResponse(
        target_id=target_id,
        hypotheses=hypotheses,
        adaptive_weights=result_data["adaptive_weights"],
        blind_spots=result_data["blind_spots"],
        recommended_types=result_data["recommended_types"],
        total_hypotheses=result_data["total_hypotheses"],
    )