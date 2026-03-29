"""API endpoints for learning metrics and adaptive tuning."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.learning import LearningMetric
from app.services.adaptive_tuning.service import adaptive_tuning_service

router = APIRouter(prefix="/learning", tags=["learning"])


class LearningMetricUpdate(BaseModel):
    target_id: str
    hypothesis_type: str
    success: bool


class LearningMetricResponse(BaseModel):
    target_id: str
    hypothesis_type: str
    success_count: int
    attempt_count: int
    success_rate: float
    last_updated: str


@router.post("/update-metric", response_model=LearningMetricResponse)
async def update_learning_metric(
    update: LearningMetricUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a learning metric based on a hypothesis test result."""
    from sqlalchemy import select, update

    # Get existing metric
    result = await db.execute(
        select(LearningMetric).where(
            LearningMetric.target_id == update.target_id,
            LearningMetric.hypothesis_type == update.hypothesis_type
        )
    )
    metric = result.scalar_one_or_none()

    if metric:
        # Update existing metric
        if update.success:
            metric.success_count += 1
        metric.attempt_count += 1
        metric.update_rate()

        # Update in database
        await db.execute(
            update(LearningMetric)
            .where(LearningMetric.id == metric.id)
            .values(
                success_count=metric.success_count,
                attempt_count=metric.attempt_count,
                success_rate=metric.success_rate,
                last_updated=metric.last_updated
            )
        )
    else:
        # Create new metric
        new_metric = LearningMetric(
            target_id=update.target_id,
            hypothesis_type=update.hypothesis_type,
            success_count=1 if update.success else 0,
            attempt_count=1,
            success_rate=1.0 if update.success else 0.0
        )
        db.add(new_metric)
        metric = new_metric

    await db.commit()
    await db.refresh(metric)

    return LearningMetricResponse(
        target_id=metric.target_id,
        hypothesis_type=metric.hypothesis_type,
        success_count=metric.success_count,
        attempt_count=metric.attempt_count,
        success_rate=metric.success_rate,
        last_updated=metric.last_updated.isoformat()
    )


@router.get("/target/{target_id}/metrics", response_model=list[LearningMetricResponse])
async def get_target_learning_metrics(
    target_id: str = Path(..., description="The target ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get all learning metrics for a target."""
    from sqlalchemy import select

    result = await db.execute(
        select(LearningMetric).where(LearningMetric.target_id == target_id)
    )
    metrics = result.scalars().all()

    return [
        LearningMetricResponse(
            target_id=m.target_id,
            hypothesis_type=m.hypothesis_type,
            success_count=m.success_count,
            attempt_count=m.attempt_count,
            success_rate=m.success_rate,
            last_updated=m.last_updated.isoformat()
        )
        for m in metrics
    ]


@router.get("/target/{target_id}/adaptive-weights")
async def get_adaptive_weights(
    target_id: str = Path(..., description="The target ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get adaptive hypothesis weights for a target."""
    weights = await adaptive_tuning_service.get_adaptive_hypothesis_weights(target_id, db)
    blind_spots = await adaptive_tuning_service.get_blind_spots(target_id, db)
    recommended = await adaptive_tuning_service.get_recommended_hypothesis_types(target_id, db, limit=10)

    return {
        "adaptive_weights": weights,
        "blind_spots": blind_spots,
        "recommended_types": recommended
    }