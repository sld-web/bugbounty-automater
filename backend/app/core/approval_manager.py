"""Approval manager for human-in-the-loop workflow."""
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import ApprovalRequest, ApprovalStatus, RiskLevel
from app.core.risk_engine import RiskEngine, RiskAssessment


class ApprovalManager:
    """Manage approval requests and workflow."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.risk_engine = RiskEngine()

    async def create_approval_request(
        self,
        action_type: str,
        action_description: str,
        target_id: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        risk_score: float = 50,
        risk_factors: dict | None = None,
        proposed_command: str | None = None,
        plugin_name: str | None = None,
        plugin_params: dict | None = None,
        evidence: dict | None = None,
        context: str | None = None,
        timeout_minutes: int = 30,
    ) -> ApprovalRequest:
        """Create a new approval request."""
        expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

        request = ApprovalRequest(
            action_type=action_type,
            action_description=action_description,
            status=ApprovalStatus.PENDING,
            target_id=target_id,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors or {},
            proposed_command=proposed_command,
            plugin_name=plugin_name,
            plugin_params=plugin_params or {},
            evidence=evidence or {},
            context=context,
            timeout_minutes=timeout_minutes,
            expires_at=expires_at,
        )

        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

        return request

    async def assess_and_create(
        self,
        action_type: str,
        action_description: str,
        target_id: str,
        target: str,
        plugin_permission: str,
        scope_info: dict | None = None,
        evidence: dict | None = None,
        context: str | None = None,
    ) -> tuple[ApprovalRequest | None, bool]:
        """Assess risk and create approval request if needed.
        
        Returns:
            Tuple of (request, should_auto_approve)
        """
        assessment = self.risk_engine.assess(
            action_type=action_type,
            target=target,
            plugin_permission=plugin_permission,
            scope_info=scope_info,
            evidence=evidence,
        )

        if assessment.auto_approve:
            return None, True

        request = await self.create_approval_request(
            action_type=action_type,
            action_description=action_description,
            target_id=target_id,
            risk_level=assessment.level,
            risk_score=assessment.score,
            risk_factors=assessment.factors,
            evidence=evidence,
            context=context,
        )

        return request, False

    async def get_pending(self) -> list[ApprovalRequest]:
        """Get all pending approval requests."""
        result = await self.db.execute(
            select(ApprovalRequest)
            .where(ApprovalRequest.status == ApprovalStatus.PENDING)
            .order_by(ApprovalRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_request(self, request_id: str) -> ApprovalRequest | None:
        """Get an approval request by ID."""
        result = await self.db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def approve(
        self,
        request_id: str,
        decided_by: str = "operator",
        modified_params: dict | None = None,
        reason: str | None = None,
    ) -> ApprovalRequest | None:
        """Approve an approval request."""
        request = await self.get_request(request_id)
        if not request:
            return None

        request.approve(
            decided_by=decided_by,
            modified_params=modified_params,
            reason=reason,
        )

        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def deny(
        self, request_id: str, decided_by: str = "operator", reason: str = ""
    ) -> ApprovalRequest | None:
        """Deny an approval request."""
        request = await self.get_request(request_id)
        if not request:
            return None

        request.deny(decided_by=decided_by, reason=reason)

        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def cancel(self, request_id: str) -> ApprovalRequest | None:
        """Cancel an approval request."""
        request = await self.get_request(request_id)
        if not request:
            return None

        request.status = ApprovalStatus.CANCELLED
        request.decided_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def process_timeouts(self) -> list[ApprovalRequest]:
        """Process expired approval requests."""
        result = await self.db.execute(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.status == ApprovalStatus.PENDING,
                ApprovalRequest.expires_at < datetime.utcnow(),
            )
        )
        expired = list(result.scalars().all())

        for request in expired:
            request.timeout()

        if expired:
            await self.db.commit()

        return expired

    async def get_queue_stats(self) -> dict:
        """Get approval queue statistics."""
        result = await self.db.execute(
            select(ApprovalRequest)
        )
        all_requests = list(result.scalars().all())

        return {
            "total": len(all_requests),
            "pending": sum(1 for r in all_requests if r.status == ApprovalStatus.PENDING),
            "approved": sum(1 for r in all_requests if r.status == ApprovalStatus.APPROVED),
            "denied": sum(1 for r in all_requests if r.status == ApprovalStatus.DENIED),
            "timed_out": sum(1 for r in all_requests if r.status == ApprovalStatus.TIMED_OUT),
            "avg_response_time_minutes": self._calc_avg_response_time(all_requests),
        }

    def _calc_avg_response_time(self, requests: list[ApprovalRequest]) -> float:
        """Calculate average response time for completed requests."""
        completed = [
            r for r in requests
            if r.status in (ApprovalStatus.APPROVED, ApprovalStatus.DENIED)
            and r.decided_at and r.created_at
        ]

        if not completed:
            return 0

        total_minutes = sum(
            (r.decided_at - r.created_at).total_seconds() / 60
            for r in completed
        )

        return round(total_minutes / len(completed), 2)
