"""Flow card API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.flow_card import FlowCard, CardStatus, CardType
from app.schemas.flow import (
    FlowCardCreate,
    FlowCardUpdate,
    FlowCardResponse,
    FlowDAGResponse,
    CoverageResponse,
)
from app.core.coverage_tracker import CoverageTracker

router = APIRouter(prefix="/flows", tags=["flows"])


@router.get("/target/{target_id}", response_model=list[FlowCardResponse])
async def list_flow_cards(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    card_type: CardType | None = None,
):
    """List flow cards for a target."""
    query = select(FlowCard).where(FlowCard.target_id == target_id)

    if card_type:
        query = query.where(FlowCard.card_type == card_type)

    query = query.order_by(FlowCard.position_y, FlowCard.position_x)
    result = await db.execute(query)
    cards = result.scalars().all()

    return [
        FlowCardResponse(
            id=c.id,
            name=c.name,
            card_type=c.card_type,
            status=c.status,
            target_id=c.target_id,
            parent_id=c.parent_id,
            description=c.description,
            card_metadata=c.card_metadata,
            position_x=c.position_x,
            position_y=c.position_y,
            results=c.results,
            logs=c.logs,
            error=c.error,
            started_at=c.started_at,
            completed_at=c.completed_at,
            duration_seconds=c.duration_seconds,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cards
    ]


@router.post("", response_model=FlowCardResponse, status_code=status.HTTP_201_CREATED)
async def create_flow_card(
    card_data: FlowCardCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new flow card."""
    card = FlowCard(
        name=card_data.name,
        card_type=card_data.card_type,
        target_id=card_data.target_id,
        parent_id=card_data.parent_id,
        description=card_data.description,
        card_metadata=card_data.card_metadata,
        position_x=card_data.position_x,
        position_y=card_data.position_y,
    )

    db.add(card)
    await db.commit()
    await db.refresh(card)

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.get("/{card_id}", response_model=FlowCardResponse)
async def get_flow_card(
    card_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific flow card."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.id == card_id)
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow card not found",
        )

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.put("/{card_id}", response_model=FlowCardResponse)
async def update_flow_card(
    card_id: str,
    card_data: FlowCardUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a flow card."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.id == card_id)
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow card not found",
        )

    update_data = card_data.model_dump(exclude_unset=True)

    if "status" in update_data:
        new_status = CardStatus(update_data["status"])
        if new_status == CardStatus.RUNNING:
            card.mark_running()
        elif new_status == CardStatus.DONE:
            card.mark_done(update_data.get("results"))
        elif new_status == CardStatus.FAILED:
            card.mark_failed(update_data.get("error", "Unknown error"))
        else:
            setattr(card, "status", new_status)

    for key, value in update_data.items():
        if key not in ("status") and hasattr(card, key):
            setattr(card, key, value)

    await db.commit()
    await db.refresh(card)

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.post("/{card_id}/start", response_model=FlowCardResponse)
async def start_flow_card(
    card_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a flow card as running."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.id == card_id)
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow card not found",
        )

    card.mark_running()
    await db.commit()
    await db.refresh(card)

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.post("/{card_id}/done", response_model=FlowCardResponse)
async def complete_flow_card(
    card_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    results: dict | None = None,
):
    """Mark a flow card as done."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.id == card_id)
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow card not found",
        )

    card.mark_done(results)
    await db.commit()
    await db.refresh(card)

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.get("/target/{target_id}/dag", response_model=FlowDAGResponse)
async def get_flow_dag(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get flow DAG for a target."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.target_id == target_id)
    )
    cards = result.scalars().all()

    edges = []
    for card in cards:
        if card.parent_id:
            edges.append({
                "id": f"{card.parent_id}-{card.id}",
                "source": card.parent_id,
                "target": card.id,
            })

    stats = {
        "total": len(cards),
        "not_started": sum(1 for c in cards if c.status == CardStatus.NOT_STARTED),
        "running": sum(1 for c in cards if c.status == CardStatus.RUNNING),
        "done": sum(1 for c in cards if c.status == CardStatus.DONE),
        "failed": sum(1 for c in cards if c.status == CardStatus.FAILED),
    }

    return FlowDAGResponse(
        target_id=target_id,
        cards=[
            FlowCardResponse(
                id=c.id,
                name=c.name,
                card_type=c.card_type,
                status=c.status,
                target_id=c.target_id,
                parent_id=c.parent_id,
                description=c.description,
                card_metadata=c.card_metadata,
                position_x=c.position_x,
                position_y=c.position_y,
                results=c.results,
                logs=c.logs,
                error=c.error,
                started_at=c.started_at,
                completed_at=c.completed_at,
                duration_seconds=c.duration_seconds,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in cards
        ],
        edges=edges,
        stats=stats,
    )
