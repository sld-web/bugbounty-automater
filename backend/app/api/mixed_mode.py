"""Mixed-mode testing API endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.mixed_mode_tester import (
    MixedModeTester,
    ProgramAccountRequestTracker,
)

router = APIRouter(prefix="/testing", tags=["mixed-mode"])


tracker = ProgramAccountRequestTracker()


class MixedModeRequest(BaseModel):
    target_id: str
    auth_level: str
    run_public_first: bool = True
    run_authenticated_if_available: bool = True
    credentials: list[dict] = []


class PhaseResultResponse(BaseModel):
    phase: str
    success: bool
    findings_count: int
    credentials_used: list[str]
    error: Optional[str] = None


class MixedModeResponse(BaseModel):
    target_id: str
    public_phase: PhaseResultResponse
    authenticated_phase: Optional[PhaseResultResponse]
    total_findings: int
    additional_findings_from_auth: int
    strategy_used: str


class AccountRequestCreate(BaseModel):
    program_id: str
    target_id: str
    contact_email: str
    scope_requested: str
    researcher_handle: str


class AccountRequestUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    credentials_id: Optional[str] = None


@router.post("/mixed-mode")
async def run_mixed_mode_testing(request: MixedModeRequest) -> MixedModeResponse:
    """Run mixed-mode testing for L1 programs.

    Strategy:
    1. Run public (unauthenticated) phase first
    2. If credentials available, run authenticated phase
    3. Return combined results with strategy used
    """
    tester = MixedModeTester()

    result = await tester.run_mixed_mode(
        target_id=request.target_id,
        run_public_first=request.run_public_first,
        run_authenticated_if_available=request.run_authenticated_if_available,
        credentials=request.credentials,
    )

    return MixedModeResponse(
        target_id=result.target_id,
        public_phase=PhaseResultResponse(
            phase=result.public_phase.phase,
            success=result.public_phase.success,
            findings_count=result.public_phase.findings_count,
            credentials_used=result.public_phase.credentials_used,
            error=result.public_phase.error,
        ),
        authenticated_phase=PhaseResultResponse(
            phase=result.authenticated_phase.phase,
            success=result.authenticated_phase.success,
            findings_count=result.authenticated_phase.findings_count,
            credentials_used=result.authenticated_phase.credentials_used,
            error=result.authenticated_phase.error,
        ) if result.authenticated_phase else None,
        total_findings=result.total_findings,
        additional_findings_from_auth=result.additional_findings_from_auth,
        strategy_used=result.strategy_used,
    )


@router.get("/mixed-mode/strategies")
async def get_testing_strategies() -> dict:
    """Get available testing strategies."""
    return {
        "strategies": [
            {
                "id": "public_only",
                "name": "Public Testing Only",
                "description": "Run without credentials",
                "use_case": "L0, L1 when no credentials available",
            },
            {
                "id": "public_plus_authenticated",
                "name": "Public + Authenticated",
                "description": "Run both phases, use credentials if available",
                "use_case": "L1 with optional credentials",
            },
            {
                "id": "authenticated_only",
                "name": "Authenticated Only",
                "description": "Skip public phase, use credentials directly",
                "use_case": "L2, L3, L4 when credentials required",
            },
            {
                "id": "public_only_auth_skipped",
                "name": "Public Only (Auth Skipped)",
                "description": "Credentials available but yielded no new findings",
                "use_case": "Results comparison after run",
            },
        ]
    }


@router.post("/account-requests")
async def create_account_request(request: AccountRequestCreate) -> dict:
    """Create a program account request for L3 programs."""
    result = tracker.create_request(
        program_id=request.program_id,
        target_id=request.target_id,
        contact_email=request.contact_email,
        scope_requested=request.scope_requested,
        researcher_handle=request.researcher_handle,
    )
    return result


@router.get("/account-requests/{request_id}")
async def get_account_request(request_id: str) -> dict:
    """Get account request status."""
    result = tracker.get_request(request_id)
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")
    return result


@router.get("/account-requests/program/{program_id}")
async def get_program_requests(program_id: str) -> dict:
    """Get all requests for a program."""
    return {
        "requests": tracker.get_requests_for_program(program_id)
    }


@router.get("/account-requests/pending")
async def get_pending_requests() -> dict:
    """Get all pending account requests."""
    return {
        "requests": tracker.get_pending_requests()
    }


@router.get("/account-requests/followup")
async def get_requests_needing_followup(days: int = Query(3, ge=1)) -> dict:
    """Get requests needing follow-up after N days."""
    return {
        "requests": tracker.get_requests_needing_followup(days)
    }


@router.patch("/account-requests/{request_id}")
async def update_account_request(
    request_id: str,
    update: AccountRequestUpdate,
) -> dict:
    """Update account request status."""
    if update.credentials_id:
        return tracker.mark_credentials_received(
            request_id=request_id,
            credentials_id=update.credentials_id,
        )

    if update.status:
        return tracker.update_status(
            request_id=request_id,
            status=update.status,
            note=update.note,
        )

    raise HTTPException(status_code=400, detail="No update provided")


@router.post("/account-requests/{request_id}/received")
async def mark_credentials_received(
    request_id: str,
    credentials_id: str,
) -> dict:
    """Mark that credentials were received for this request."""
    return tracker.mark_credentials_received(
        request_id=request_id,
        credentials_id=credentials_id,
    )
