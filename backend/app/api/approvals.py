"""Approval API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.approval_manager import ApprovalManager
from app.models.approval import ApprovalRequest, ApprovalStatus
from app.schemas.approval import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalDecision,
    ApprovalListResponse,
    ApprovalQueueResponse,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    status_filter: ApprovalStatus | None = None,
    target_id: str | None = None,
):
    """List approval requests."""
    query = select(ApprovalRequest)

    if status_filter:
        query = query.where(ApprovalRequest.status == status_filter)
    if target_id:
        query = query.where(ApprovalRequest.target_id == target_id)

    total = len((await db.execute(query)).scalars().all())

    query = query.offset(skip).limit(limit).order_by(ApprovalRequest.created_at.desc())
    result = await db.execute(query)
    approvals = result.scalars().all()

    pending_count = len(
        (await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.status == ApprovalStatus.PENDING)
        )).scalars().all()
    )

    return ApprovalListResponse(
        items=[
            ApprovalRequestResponse(
                id=a.id,
                action_type=a.action_type,
                action_description=a.action_description,
                status=a.status,
                target_id=a.target_id,
                risk_level=a.risk_level,
                risk_score=a.risk_score,
                risk_factors=a.risk_factors,
                proposed_command=a.proposed_command,
                plugin_name=a.plugin_name,
                plugin_params=a.plugin_params,
                evidence=a.evidence,
                context=a.context,
                decided_by=a.decided_by,
                decided_at=a.decided_at,
                decision_reason=a.decision_reason,
                modified_params=a.modified_params,
                timeout_minutes=a.timeout_minutes,
                expires_at=a.expires_at,
                notified_at=a.notified_at,
                notification_channel=a.notification_channel,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in approvals
        ],
        total=total,
        pending_count=pending_count,
    )


@router.get("/queue", response_model=ApprovalQueueResponse)
async def get_approval_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get approval queue overview."""
    manager = ApprovalManager(db)

    pending = await manager.get_pending()
    stats = await manager.get_queue_stats()

    result = await db.execute(
        select(ApprovalRequest)
        .where(ApprovalRequest.status.in_([ApprovalStatus.APPROVED, ApprovalStatus.DENIED]))
        .order_by(ApprovalRequest.decided_at.desc())
        .limit(10)
    )
    recent = result.scalars().all()

    return ApprovalQueueResponse(
        pending=[
            ApprovalRequestResponse(
                id=a.id,
                action_type=a.action_type,
                action_description=a.action_description,
                status=a.status,
                target_id=a.target_id,
                risk_level=a.risk_level,
                risk_score=a.risk_score,
                risk_factors=a.risk_factors,
                proposed_command=a.proposed_command,
                plugin_name=a.plugin_name,
                plugin_params=a.plugin_params,
                evidence=a.evidence,
                context=a.context,
                decided_by=a.decided_by,
                decided_at=a.decided_at,
                decision_reason=a.decision_reason,
                modified_params=a.modified_params,
                timeout_minutes=a.timeout_minutes,
                expires_at=a.expires_at,
                notified_at=a.notified_at,
                notification_channel=a.notification_channel,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in pending
        ],
        recent=[
            ApprovalRequestResponse(
                id=a.id,
                action_type=a.action_type,
                action_description=a.action_description,
                status=a.status,
                target_id=a.target_id,
                risk_level=a.risk_level,
                risk_score=a.risk_score,
                risk_factors=a.risk_factors,
                proposed_command=a.proposed_command,
                plugin_name=a.plugin_name,
                plugin_params=a.plugin_params,
                evidence=a.evidence,
                context=a.context,
                decided_by=a.decided_by,
                decided_at=a.decided_at,
                decision_reason=a.decision_reason,
                modified_params=a.modified_params,
                timeout_minutes=a.timeout_minutes,
                expires_at=a.expires_at,
                notified_at=a.notified_at,
                notification_channel=a.notification_channel,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in recent
        ],
        stats=stats,
    )


@router.get("/{approval_id}", response_model=ApprovalRequestResponse)
async def get_approval(
    approval_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific approval request."""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    return ApprovalRequestResponse(
        id=approval.id,
        action_type=approval.action_type,
        action_description=approval.action_description,
        status=approval.status,
        target_id=approval.target_id,
        risk_level=approval.risk_level,
        risk_score=approval.risk_score,
        risk_factors=approval.risk_factors,
        proposed_command=approval.proposed_command,
        plugin_name=approval.plugin_name,
        plugin_params=approval.plugin_params,
        evidence=approval.evidence,
        context=approval.context,
        decided_by=approval.decided_by,
        decided_at=approval.decided_at,
        decision_reason=approval.decision_reason,
        modified_params=approval.modified_params,
        timeout_minutes=approval.timeout_minutes,
        expires_at=approval.expires_at,
        notified_at=approval.notified_at,
        notification_channel=approval.notification_channel,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
    )


@router.post("/{approval_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(
    approval_id: str,
    decision: ApprovalDecision,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Approve an approval request."""
    if decision.decision != "approve":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use deny endpoint to reject requests",
        )

    manager = ApprovalManager(db)
    approval = await manager.approve(
        request_id=approval_id,
        decided_by=decision.decided_by,
        modified_params=decision.modified_params,
        reason=decision.reason,
    )

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    return ApprovalRequestResponse(
        id=approval.id,
        action_type=approval.action_type,
        action_description=approval.action_description,
        status=approval.status,
        target_id=approval.target_id,
        risk_level=approval.risk_level,
        risk_score=approval.risk_score,
        risk_factors=approval.risk_factors,
        proposed_command=approval.proposed_command,
        plugin_name=approval.plugin_name,
        plugin_params=approval.plugin_params,
        evidence=approval.evidence,
        context=approval.context,
        decided_by=approval.decided_by,
        decided_at=approval.decided_at,
        decision_reason=approval.decision_reason,
        modified_params=approval.modified_params,
        timeout_minutes=approval.timeout_minutes,
        expires_at=approval.expires_at,
        notified_at=approval.notified_at,
        notification_channel=approval.notification_channel,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
    )


@router.post("/{approval_id}/deny", response_model=ApprovalRequestResponse)
async def deny_request(
    approval_id: str,
    decision: ApprovalDecision,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Deny an approval request."""
    if decision.decision != "deny":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use approve endpoint to accept requests",
        )

    manager = ApprovalManager(db)
    approval = await manager.deny(
        request_id=approval_id,
        decided_by=decision.decided_by,
        reason=decision.reason or "",
    )

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    return ApprovalRequestResponse(
        id=approval.id,
        action_type=approval.action_type,
        action_description=approval.action_description,
        status=approval.status,
        target_id=approval.target_id,
        risk_level=approval.risk_level,
        risk_score=approval.risk_score,
        risk_factors=approval.risk_factors,
        proposed_command=approval.proposed_command,
        plugin_name=approval.plugin_name,
        plugin_params=approval.plugin_params,
        evidence=approval.evidence,
        context=approval.context,
        decided_by=approval.decided_by,
        decided_at=approval.decided_at,
        decision_reason=approval.decision_reason,
        modified_params=approval.modified_params,
        timeout_minutes=approval.timeout_minutes,
        expires_at=approval.expires_at,
        notified_at=approval.notified_at,
        notification_channel=approval.notification_channel,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
    )


@router.post("/{approval_id}/timeout", response_model=ApprovalRequestResponse)
async def timeout_request(
    approval_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Manually trigger timeout for an approval request."""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    approval.timeout()
    await db.commit()
    await db.refresh(approval)

    return ApprovalRequestResponse(
        id=approval.id,
        action_type=approval.action_type,
        action_description=approval.action_description,
        status=approval.status,
        target_id=approval.target_id,
        risk_level=approval.risk_level,
        risk_score=approval.risk_score,
        risk_factors=approval.risk_factors,
        proposed_command=approval.proposed_command,
        plugin_name=approval.plugin_name,
        plugin_params=approval.plugin_params,
        evidence=approval.evidence,
        context=approval.context,
        decided_by=approval.decided_by,
        decided_at=approval.decided_at,
        decision_reason=approval.decision_reason,
        modified_params=approval.modified_params,
        timeout_minutes=approval.timeout_minutes,
        expires_at=approval.expires_at,
        notified_at=approval.notified_at,
        notification_channel=approval.notification_channel,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
    )
