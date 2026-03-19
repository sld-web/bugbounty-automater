"""Program API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.program import Program
from app.models.target import Target
from app.schemas.program import (
    ProgramCreate,
    ProgramUpdate,
    ProgramResponse,
    ProgramConfigResponse,
    ScopeConfig,
)

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=list[ProgramResponse])
async def list_programs(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    platform: str | None = None,
    needs_review: bool | None = None,
):
    """List all programs."""
    query = select(Program).options(selectinload(Program.targets))

    if platform:
        query = query.where(Program.platform == platform)
    if needs_review is not None:
        query = query.where(Program.needs_review == needs_review)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    programs = result.scalars().all()

    response = []
    for program in programs:
        target_count = len(program.targets)
        finding_count = 0  # Skip for now to avoid lazy loading issues

        response.append(
            ProgramResponse(
                id=program.id,
                name=program.name,
                platform=program.platform,
                url=program.url,
                scope=ScopeConfig(
                    domains=program.scope_domains,
                    excluded=program.scope_excluded,
                    mobile_apps=program.scope_mobile_apps,
                    repositories=program.scope_repositories,
                ),
                priority_areas=program.priority_areas,
                out_of_scope=program.out_of_scope,
                severity_mapping=program.severity_mapping,
                reward_tiers=program.reward_tiers,
                campaigns=[],
                special_requirements=program.special_requirements,
                confidence_score=program.confidence_score,
                needs_review=program.needs_review,
                reviewed_at=program.reviewed_at,
                review_notes=program.review_notes,
                created_at=program.created_at,
                updated_at=program.updated_at,
                target_count=target_count,
                finding_count=finding_count,
            )
        )

    return response


@router.get("/{program_id}", response_model=ProgramResponse)
async def get_program(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific program."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    return ProgramResponse(
        id=program.id,
        name=program.name,
        platform=program.platform,
        url=program.url,
        scope=ScopeConfig(
            domains=program.scope_domains,
            excluded=program.scope_excluded,
            mobile_apps=program.scope_mobile_apps,
            repositories=program.scope_repositories,
        ),
        priority_areas=program.priority_areas,
        out_of_scope=program.out_of_scope,
        severity_mapping=program.severity_mapping,
        reward_tiers=program.reward_tiers,
        campaigns=[],
        special_requirements=program.special_requirements,
        confidence_score=program.confidence_score,
        needs_review=program.needs_review,
        reviewed_at=program.reviewed_at,
        review_notes=program.review_notes,
        created_at=program.created_at,
        updated_at=program.updated_at,
        target_count=len(program.targets),
        finding_count=sum(len(t.findings) for t in program.targets),
    )


@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    program_data: ProgramCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new program."""
    existing = await db.execute(
        select(Program).where(Program.name == program_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Program with this name already exists",
        )

    program = Program(
        name=program_data.name,
        platform=program_data.platform,
        url=program_data.url,
        raw_policy=program_data.raw_policy,
        scope_domains=program_data.scope.domains,
        scope_excluded=program_data.scope.excluded,
        scope_mobile_apps=program_data.scope.mobile_apps,
        scope_repositories=program_data.scope.repositories,
        priority_areas=program_data.priority_areas,
        out_of_scope=program_data.out_of_scope,
        severity_mapping=program_data.severity_mapping,
        reward_tiers=program_data.reward_tiers,
        campaigns=[c.model_dump() for c in program_data.campaigns],
        special_requirements=program_data.special_requirements,
    )

    db.add(program)
    await db.commit()
    await db.refresh(program)

    return ProgramResponse(
        id=program.id,
        name=program.name,
        platform=program.platform,
        url=program.url,
        scope=program_data.scope,
        priority_areas=program.priority_areas,
        out_of_scope=program.out_of_scope,
        severity_mapping=program.severity_mapping,
        reward_tiers=program.reward_tiers,
        campaigns=program_data.campaigns,
        special_requirements=program.special_requirements,
        confidence_score=0,
        needs_review=True,
        reviewed_at=None,
        review_notes=None,
        created_at=program.created_at,
        updated_at=program.updated_at,
        target_count=0,
        finding_count=0,
    )


@router.put("/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: str,
    program_data: ProgramUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a program."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    update_data = program_data.model_dump(exclude_unset=True)

    if "scope" in update_data:
        scope = update_data.pop("scope")
        if scope:
            program.scope_domains = scope.get("domains", program.scope_domains)
            program.scope_excluded = scope.get("excluded", program.scope_excluded)
            program.scope_mobile_apps = scope.get("mobile_apps", program.scope_mobile_apps)
            program.scope_repositories = scope.get("repositories", program.scope_repositories)

    if "reviewed" in update_data:
        program.needs_review = not update_data["reviewed"]
        program.reviewed_at = program.created_at

    for key, value in update_data.items():
        if hasattr(program, key) and key not in ("scope", "reviewed"):
            setattr(program, key, value)

    await db.commit()
    await db.refresh(program)

    return ProgramResponse(
        id=program.id,
        name=program.name,
        platform=program.platform,
        url=program.url,
        scope=ScopeConfig(
            domains=program.scope_domains,
            excluded=program.scope_excluded,
            mobile_apps=program.scope_mobile_apps,
            repositories=program.scope_repositories,
        ),
        priority_areas=program.priority_areas,
        out_of_scope=program.out_of_scope,
        severity_mapping=program.severity_mapping,
        reward_tiers=program.reward_tiers,
        campaigns=[],
        special_requirements=program.special_requirements,
        confidence_score=program.confidence_score,
        needs_review=program.needs_review,
        reviewed_at=program.reviewed_at,
        review_notes=program.review_notes,
        created_at=program.created_at,
        updated_at=program.updated_at,
        target_count=len(program.targets),
        finding_count=sum(len(t.findings) for t in program.targets),
    )


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a program."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    await db.delete(program)
    await db.commit()


@router.get("/{program_id}/config", response_model=ProgramConfigResponse)
async def get_program_config(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get program configuration for orchestration."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    return ProgramConfigResponse(
        program_id=program.id,
        program_name=program.name,
        scope=ScopeConfig(
            domains=program.scope_domains,
            excluded=program.scope_excluded,
            mobile_apps=program.scope_mobile_apps,
            repositories=program.scope_repositories,
        ),
        priority_areas=program.priority_areas,
        out_of_scope=program.out_of_scope,
        severity_mapping=program.severity_mapping,
        reward_tiers=program.reward_tiers,
        campaigns=[],
        special_requirements=program.special_requirements,
        confidence_score=program.confidence_score,
    )
