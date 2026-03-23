"""Target API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.orchestrator import Orchestrator
from app.models.target import Target, TargetStatus, TargetType
from app.schemas.target import (
    TargetCreate,
    TargetUpdate,
    TargetResponse,
    TargetStatusResponse,
    TargetListResponse,
)

router = APIRouter(prefix="/targets", tags=["targets"])


@router.get("", response_model=TargetListResponse)
async def list_targets(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    program_id: str | None = None,
    status_filter: TargetStatus | None = None,
):
    """List all targets."""
    query = select(Target).options(selectinload(Target.program))

    if program_id:
        query = query.where(Target.program_id == program_id)
    if status_filter:
        query = query.where(Target.status == status_filter)

    count_query = select(Target)
    if program_id:
        count_query = count_query.where(Target.program_id == program_id)
    if status_filter:
        count_query = count_query.where(Target.status == status_filter)

    total_result = await db.execute(
        select(Target.id).where(
            Target.id.in_(
                [r.id for r in (await db.execute(count_query)).scalars().all()]
            )
        )
    )
    total = len((await db.execute(count_query)).scalars().all())

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    targets = result.scalars().all()

    items = [
        TargetResponse(
            id=t.id,
            name=t.name,
            target_type=t.target_type,
            status=t.status,
            program_id=t.program_id,
            technologies=t.technologies,
            ports=t.ports,
            subdomains=t.subdomains,
            endpoints=t.endpoints,
            target_metadata=t.target_metadata,
            surface_coverage=t.surface_coverage,
            attack_vector_coverage=t.attack_vector_coverage,
            logic_flow_coverage=t.logic_flow_coverage,
            error_message=t.error_message,
            retry_count=t.retry_count,
            created_at=t.created_at,
            updated_at=t.updated_at,
            program_name=t.program.name if t.program else None,
        )
        for t in targets
    ]

    return TargetListResponse(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific target."""
    result = await db.execute(
        select(Target)
        .options(selectinload(Target.program))
        .where(Target.id == target_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    return TargetResponse(
        id=target.id,
        name=target.name,
        target_type=target.target_type,
        status=target.status,
        program_id=target.program_id,
        technologies=target.technologies,
        ports=target.ports,
        subdomains=target.subdomains,
        endpoints=target.endpoints,
        target_metadata=target.target_metadata,
        surface_coverage=target.surface_coverage,
        attack_vector_coverage=target.attack_vector_coverage,
        logic_flow_coverage=target.logic_flow_coverage,
        error_message=target.error_message,
        retry_count=target.retry_count,
        created_at=target.created_at,
        updated_at=target.updated_at,
        program_name=target.program.name if target.program else None,
    )


@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new target."""
    from app.models.program import Program

    program_result = await db.execute(
        select(Program).where(Program.id == target_data.program_id)
    )
    program = program_result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Program not found",
        )

    if not program.is_in_scope(target_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target is not in program scope",
        )

    target = Target(
        name=target_data.name,
        target_type=target_data.target_type,
        program_id=target_data.program_id,
        target_metadata=target_data.target_metadata,
    )

    db.add(target)
    await db.commit()
    await db.refresh(target)

    return TargetResponse(
        id=target.id,
        name=target.name,
        target_type=target.target_type,
        status=target.status,
        program_id=target.program_id,
        technologies=target.technologies,
        ports=target.ports,
        subdomains=target.subdomains,
        endpoints=target.endpoints,
        target_metadata=target.target_metadata,
        surface_coverage=target.surface_coverage,
        attack_vector_coverage=target.attack_vector_coverage,
        logic_flow_coverage=target.logic_flow_coverage,
        error_message=target.error_message,
        retry_count=target.retry_count,
        created_at=target.created_at,
        updated_at=target.updated_at,
        program_name=program.name,
    )


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: str,
    target_data: TargetUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a target."""
    result = await db.execute(
        select(Target)
        .options(selectinload(Target.program))
        .where(Target.id == target_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    update_data = target_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(target, key):
            setattr(target, key, value)

    await db.commit()
    await db.refresh(target)

    return TargetResponse(
        id=target.id,
        name=target.name,
        target_type=target.target_type,
        status=target.status,
        program_id=target.program_id,
        technologies=target.technologies,
        ports=target.ports,
        subdomains=target.subdomains,
        endpoints=target.endpoints,
        target_metadata=target.target_metadata,
        surface_coverage=target.surface_coverage,
        attack_vector_coverage=target.attack_vector_coverage,
        logic_flow_coverage=target.logic_flow_coverage,
        error_message=target.error_message,
        retry_count=target.retry_count,
        created_at=target.created_at,
        updated_at=target.updated_at,
        program_name=target.program.name if target.program else None,
    )


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a target."""
    result = await db.execute(
        select(Target).where(Target.id == target_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    await db.delete(target)
    await db.commit()


@router.post("/{target_id}/start", response_model=TargetResponse)
async def start_target(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Start the testing pipeline for a target."""
    orchestrator = Orchestrator(db)
    try:
        target = await orchestrator.start_target(target_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
            )
    return TargetResponse(
        id=target.id,
        name=target.name,
        target_type=target.target_type,
        status=target.status,
        program_id=target.program_id,
        technologies=target.technologies,
        ports=target.ports,
        subdomains=target.subdomains,
        endpoints=target.endpoints,
        target_metadata=target.target_metadata,
        surface_coverage=target.surface_coverage,
        attack_vector_coverage=target.attack_vector_coverage,
        logic_flow_coverage=target.logic_flow_coverage,
        error_message=target.error_message,
        retry_count=target.retry_count,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )


@router.post("/{target_id}/pause", response_model=TargetResponse)
async def pause_target(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Pause a running target."""
    orchestrator = Orchestrator(db)
    target = await orchestrator.pause_target(target_id)
    return TargetResponse(
        id=target.id,
        name=target.name,
        target_type=target.target_type,
        status=target.status,
        program_id=target.program_id,
        technologies=target.technologies,
        ports=target.ports,
        subdomains=target.subdomains,
        endpoints=target.endpoints,
        target_metadata=target.target_metadata,
        surface_coverage=target.surface_coverage,
        attack_vector_coverage=target.attack_vector_coverage,
        logic_flow_coverage=target.logic_flow_coverage,
        error_message=target.error_message,
        retry_count=target.retry_count,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )


@router.post("/{target_id}/resume", response_model=TargetResponse)
async def resume_target(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Resume a paused target."""
    orchestrator = Orchestrator(db)
    target = await orchestrator.resume_target(target_id)
    return TargetResponse(
        id=target.id,
        name=target.name,
        target_type=target.target_type,
        status=target.status,
        program_id=target.program_id,
        technologies=target.technologies,
        ports=target.ports,
        subdomains=target.subdomains,
        endpoints=target.endpoints,
        target_metadata=target.target_metadata,
        surface_coverage=target.surface_coverage,
        attack_vector_coverage=target.attack_vector_coverage,
        logic_flow_coverage=target.logic_flow_coverage,
        error_message=target.error_message,
        retry_count=target.retry_count,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )


@router.get("/{target_id}/status", response_model=TargetStatusResponse)
async def get_target_status(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get target status."""
    result = await db.execute(
        select(Target).where(Target.id == target_id)
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    return TargetStatusResponse(
        id=target.id,
        status=target.status,
        error_message=target.error_message,
        retry_count=target.retry_count,
        surface_coverage=target.surface_coverage,
        attack_vector_coverage=target.attack_vector_coverage,
        logic_flow_coverage=target.logic_flow_coverage,
    )
