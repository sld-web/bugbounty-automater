"""Mixed-mode testing service for L1 optional authentication programs."""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PhaseResult:
    phase: str
    success: bool
    findings_count: int
    credentials_used: list[str]
    error: Optional[str] = None


@dataclass
class MixedModeResult:
    target_id: str
    public_phase: PhaseResult
    authenticated_phase: Optional[PhaseResult]
    total_findings: int
    additional_findings_from_auth: int
    strategy_used: str


class MixedModeTester:
    """Handles mixed-mode testing for L1 programs."""

    def __init__(self):
        self.phase_results: list[PhaseResult] = []

    async def run_mixed_mode(
        self,
        target_id: str,
        run_public_first: bool = True,
        run_authenticated_if_available: bool = True,
        public_phase_func=None,
        authenticated_phase_func=None,
        credentials: list[dict] = None,
    ) -> MixedModeResult:
        """Run mixed-mode testing.

        Strategy:
        1. Always run public phase first (if enabled)
        2. If authenticated phase enabled and creds available, run it
        3. Compare results
        """
        credentials = credentials or []
        valid_creds = [c for c in credentials if c.get("is_active", True) and not c.get("is_expired", False)]

        self.phase_results = []
        public_phase = PhaseResult(
            phase="public",
            success=False,
            findings_count=0,
            credentials_used=[],
        )
        authenticated_phase = None

        if run_public_first:
            logger.info(f"[{target_id}] Running public (unauthenticated) phase")
            if public_phase_func:
                try:
                    public_result = await public_phase_func(target_id)
                    public_phase = PhaseResult(
                        phase="public",
                        success=True,
                        findings_count=public_result.get("findings", 0),
                        credentials_used=[],
                    )
                except Exception as e:
                    public_phase = PhaseResult(
                        phase="public",
                        success=False,
                        findings_count=0,
                        credentials_used=[],
                        error=str(e),
                    )
            else:
                public_phase.success = True
                public_phase.findings_count = 0

        if run_authenticated_if_available and valid_creds:
            logger.info(f"[{target_id}] Running authenticated phase with {len(valid_creds)} credentials")
            if authenticated_phase_func:
                try:
                    auth_result = await authenticated_phase_func(
                        target_id,
                        credential_ids=[c.get("id") for c in valid_creds],
                    )
                    authenticated_phase = PhaseResult(
                        phase="authenticated",
                        success=True,
                        findings_count=auth_result.get("findings", 0),
                        credentials_used=[c.get("id") for c in valid_creds],
                    )
                except Exception as e:
                    authenticated_phase = PhaseResult(
                        phase="authenticated",
                        success=False,
                        findings_count=0,
                        credentials_used=[c.get("id") for c in valid_creds],
                        error=str(e),
                    )
            else:
                authenticated_phase = PhaseResult(
                    phase="authenticated",
                    success=True,
                    findings_count=0,
                    credentials_used=[c.get("id") for c in valid_creds],
                )
        elif run_authenticated_if_available and not valid_creds:
            logger.info(f"[{target_id}] Skipping authenticated phase - no valid credentials")
            authenticated_phase = PhaseResult(
                phase="authenticated",
                success=True,
                findings_count=0,
                credentials_used=[],
                error="No valid credentials available",
            )

        total_findings = public_phase.findings_count
        if authenticated_phase:
            total_findings += authenticated_phase.findings_count

        additional_findings = 0
        if authenticated_phase:
            additional_findings = authenticated_phase.findings_count

        strategy = "public_only"
        if authenticated_phase and authenticated_phase.findings_count > 0:
            strategy = "public_plus_authenticated"
        elif authenticated_phase and authenticated_phase.findings_count == 0:
            strategy = "public_only_auth_skipped"
        elif authenticated_phase:
            strategy = "authenticated_only"

        return MixedModeResult(
            target_id=target_id,
            public_phase=public_phase,
            authenticated_phase=authenticated_phase,
            total_findings=total_findings,
            additional_findings_from_auth=additional_findings,
            strategy_used=strategy,
        )

    def compare_results(
        self,
        public_findings: list[dict],
        auth_findings: list[dict],
    ) -> dict:
        """Compare public vs authenticated findings."""
        public_urls = {f.get("url") for f in public_findings}
        auth_urls = {f.get("url") for f in auth_findings}

        public_only = public_urls - auth_urls
        auth_only = auth_urls - public_urls
        common = public_urls & auth_urls

        return {
            "public_findings": len(public_findings),
            "authenticated_findings": len(auth_findings),
            "public_only_count": len(public_only),
            "auth_only_count": len(auth_only),
            "common_count": len(common),
            "public_only_urls": list(public_only),
            "auth_only_urls": list(auth_only),
            "additional_coverage": len(auth_only) > 0,
            "recommendation": self._get_recommendation(len(auth_only), len(common)),
        }

    def _get_recommendation(self, auth_only_count: int, common_count: int) -> str:
        """Generate recommendation based on findings."""
        if auth_only_count == 0 and common_count == 0:
            return "No findings in either phase. Consider deeper testing."
        elif auth_only_count > 0:
            return (
                f"Found {auth_only_count} additional findings with authenticated testing. "
                "Always use test accounts for comprehensive coverage."
            )
        elif common_count > 0:
            return (
                "All public findings also found in authenticated testing. "
                "Consider if credentials add value for this target."
            )
        return "Testing complete. Review findings for duplicate entries."


class ProgramAccountRequestTracker:
    """Track program-provided account requests."""

    def __init__(self):
        self.requests: dict[str, dict] = {}

    def create_request(
        self,
        program_id: str,
        target_id: str,
        contact_email: str,
        scope_requested: str,
        researcher_handle: str,
    ) -> dict:
        """Create a new program account request."""
        import uuid
        request_id = str(uuid.uuid4())

        request = {
            "id": request_id,
            "program_id": program_id,
            "target_id": target_id,
            "contact_email": contact_email,
            "scope_requested": scope_requested,
            "researcher_handle": researcher_handle,
            "status": "pending",
            "created_at": str(asyncio.get_event_loop().time()),
            "last_updated": str(asyncio.get_event_loop().time()),
            "credentials_received": False,
            "credentials_id": None,
            "notes": [],
        }

        self.requests[request_id] = request
        logger.info(f"Created account request {request_id} for program {program_id}")

        return request

    def update_status(
        self,
        request_id: str,
        status: str,
        note: str = None,
    ) -> dict:
        """Update request status."""
        if request_id not in self.requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.requests[request_id]
        old_status = request["status"]
        request["status"] = status
        request["last_updated"] = str(asyncio.get_event_loop().time())

        if note:
            request["notes"].append({
                "note": note,
                "timestamp": str(asyncio.get_event_loop().time()),
            })

        logger.info(f"Updated request {request_id}: {old_status} -> {status}")

        return request

    def mark_credentials_received(
        self,
        request_id: str,
        credentials_id: str,
    ) -> dict:
        """Mark that credentials were received for this request."""
        if request_id not in self.requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.requests[request_id]
        request["credentials_received"] = True
        request["credentials_id"] = credentials_id
        request["last_updated"] = str(asyncio.get_event_loop().time())
        request["status"] = "credentials_received"

        request["notes"].append({
            "note": f"Credentials received and stored: {credentials_id}",
            "timestamp": str(asyncio.get_event_loop().time()),
        })

        logger.info(f"Credentials received for request {request_id}")

        return request

    def get_request(self, request_id: str) -> dict:
        """Get a specific request."""
        return self.requests.get(request_id)

    def get_requests_for_program(self, program_id: str) -> list[dict]:
        """Get all requests for a program."""
        return [
            r for r in self.requests.values()
            if r["program_id"] == program_id
        ]

    def get_pending_requests(self) -> list[dict]:
        """Get all pending requests."""
        return [
            r for r in self.requests.values()
            if r["status"] in ["pending", "sent"]
        ]

    def get_requests_needing_followup(self, days: int = 3) -> list[dict]:
        """Get requests that haven't received a response after N days."""
        import time
        cutoff = time.time() - (days * 86400)

        return [
            r for r in self.requests.values()
            if r["status"] in ["pending", "sent"]
            and float(r["last_updated"]) < cutoff
        ]
