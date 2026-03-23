"""Credential Decision Engine - Determines auth requirements per program level."""
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class AuthLevel(str, Enum):
    L0_NONE = "none"
    L1_OPTIONAL = "optional"
    L2_REQUIRED = "required"
    L3_PROGRAM_PROVIDED = "program_provided"
    L4_DOMAIN_VALIDATED = "domain_validated"


class CredentialStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    NEAR_EXPIRY = "near_expiry"
    NOT_FOUND = "not_found"


@dataclass
class CredentialDecision:
    level: AuthLevel
    can_proceed: bool
    requires_credentials: bool
    message: str
    credential_ids: list[str] = None
    missing_info: list[str] = None
    approval_required: bool = False


@dataclass
class CredentialTestResult:
    credential_id: str
    status: CredentialStatus
    message: str
    can_authenticate: bool
    response_time_ms: Optional[float] = None


class CredentialDecisionEngine:
    """Determines authentication requirements based on program configuration."""

    DOMAIN_PATTERNS = {
        "hackerone": r"@hackerone\.com$",
        "bugcrowd": r"@bugcrowd\.com$",
        "openbugbounty": r"@openbugbounty\.org$",
        "syndicate": r"@syndicate\.xyz$",
        "yeswehack": r"@yeswehack\.com$",
        "hackernone": r"@hackernone\.com$",
    }

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()

    def get_decision(
        self,
        auth_level: str,
        credentials: list[dict] = None,
        program_domain: str = None,
        user_email: str = None,
    ) -> CredentialDecision:
        """Get credential decision based on auth level and available credentials."""
        credentials = credentials or []
        credential_ids = [c.get("id") for c in credentials if c.get("is_active", True)]

        if auth_level == AuthLevel.L0_NONE:
            return self._handle_l0(credentials)

        elif auth_level == AuthLevel.L1_OPTIONAL:
            return self._handle_l1(credentials, credential_ids)

        elif auth_level == AuthLevel.L2_REQUIRED:
            return self._handle_l2(credentials, credential_ids)

        elif auth_level == AuthLevel.L3_PROGRAM_PROVIDED:
            return self._handle_l3(credentials, credential_ids)

        elif auth_level == AuthLevel.L4_DOMAIN_VALIDATED:
            return self._handle_l4(
                credentials,
                credential_ids,
                program_domain,
                user_email,
            )

        return CredentialDecision(
            level=AuthLevel.L0_NONE,
            can_proceed=True,
            requires_credentials=False,
            message="Unknown auth level, proceeding without credentials",
        )

    def _handle_l0(self, credentials: list[dict]) -> CredentialDecision:
        """L0: No authentication required."""
        return CredentialDecision(
            level=AuthLevel.L0_NONE,
            can_proceed=True,
            requires_credentials=False,
            message="L0: No authentication required. Proceeding with public testing only.",
        )

    def _handle_l1(
        self, credentials: list[dict], credential_ids: list[str]
    ) -> CredentialDecision:
        """L1: Optional authentication."""
        if not credentials:
            return CredentialDecision(
                level=AuthLevel.L1_OPTIONAL,
                can_proceed=True,
                requires_credentials=False,
                message="L1: No credentials provided. Proceeding with public testing only. "
                "Would you like to add credentials for authenticated testing?",
            )

        valid_creds = [c for c in credentials if not c.get("is_expired", False)]
        if not valid_creds:
            return CredentialDecision(
                level=AuthLevel.L1_OPTIONAL,
                can_proceed=True,
                requires_credentials=False,
                message="L1: All credentials expired. Proceeding with public testing only.",
                credential_ids=credential_ids,
                missing_info=["valid_credentials"],
            )

        return CredentialDecision(
            level=AuthLevel.L1_OPTIONAL,
            can_proceed=True,
            requires_credentials=False,
            message="L1: Credentials available. Proceeding with authenticated testing.",
            credential_ids=credential_ids,
        )

    def _handle_l2(
        self, credentials: list[dict], credential_ids: list[str]
    ) -> CredentialDecision:
        """L2: Required authentication."""
        if not credentials:
            return CredentialDecision(
                level=AuthLevel.L2_REQUIRED,
                can_proceed=False,
                requires_credentials=True,
                message="L2: Authentication required. Testing blocked until credentials provided.",
                missing_info=["credentials"],
                approval_required=False,
            )

        valid_creds = [c for c in credentials if not c.get("is_expired", False)]
        if not valid_creds:
            return CredentialDecision(
                level=AuthLevel.L2_REQUIRED,
                can_proceed=False,
                requires_credentials=True,
                message="L2: All credentials expired. Please provide valid credentials.",
                credential_ids=credential_ids,
                missing_info=["valid_credentials"],
            )

        return CredentialDecision(
            level=AuthLevel.L2_REQUIRED,
            can_proceed=True,
            requires_credentials=True,
            message="L2: Valid credentials found. Proceeding with authenticated testing.",
            credential_ids=credential_ids,
        )

    def _handle_l3(
        self, credentials: list[dict], credential_ids: list[str]
    ) -> CredentialDecision:
        """L3: Program-provided account required."""
        program_provided = [
            c for c in credentials if c.get("source") == "program"
        ]

        if not program_provided:
            return CredentialDecision(
                level=AuthLevel.L3_PROGRAM_PROVIDED,
                can_proceed=False,
                requires_credentials=True,
                message="L3: Program-provided account required. "
                "Request access through the program's bug bounty platform.",
                missing_info=["program_provided_account"],
                approval_required=True,
            )

        valid_provided = [c for c in program_provided if not c.get("is_expired", False)]
        if not valid_provided:
            return CredentialDecision(
                level=AuthLevel.L3_PROGRAM_PROVIDED,
                can_proceed=False,
                requires_credentials=True,
                message="L3: Program-provided account has expired. Request a new one.",
                credential_ids=[c.get("id") for c in program_provided],
                missing_info=["valid_program_account"],
                approval_required=True,
            )

        return CredentialDecision(
            level=AuthLevel.L3_PROGRAM_PROVIDED,
            can_proceed=True,
            requires_credentials=True,
            message="L3: Program-provided account available. Proceeding.",
            credential_ids=[c.get("id") for c in valid_provided],
        )

    def _handle_l4(
        self,
        credentials: list[dict],
        credential_ids: list[str],
        program_domain: str,
        user_email: str,
    ) -> CredentialDecision:
        """L4: Domain-validated email required."""
        if not credentials:
            return CredentialDecision(
                level=AuthLevel.L4_DOMAIN_VALIDATED,
                can_proceed=False,
                requires_credentials=True,
                message="L4: Bug bounty program requires valid email registration. "
                f"Please register with {program_domain} domain.",
                missing_info=["registered_email"],
            )

        valid_creds = [c for c in credentials if not c.get("is_expired", False)]
        if not valid_creds:
            return CredentialDecision(
                level=AuthLevel.L4_DOMAIN_VALIDATED,
                can_proceed=False,
                requires_credentials=True,
                message="L4: All credentials expired. Please update your credentials.",
                credential_ids=credential_ids,
                missing_info=["valid_domain_credential"],
            )

        if program_domain and user_email:
            if not self._validate_email_domain(user_email, program_domain):
                return CredentialDecision(
                    level=AuthLevel.L4_DOMAIN_VALIDATED,
                    can_proceed=False,
                    requires_credentials=True,
                    message=f"L4: Email must be from {program_domain} domain. "
                    f"Current: {user_email}",
                    credential_ids=credential_ids,
                    missing_info=["valid_domain_email"],
                )

        return CredentialDecision(
            level=AuthLevel.L4_DOMAIN_VALIDATED,
            can_proceed=True,
            requires_credentials=True,
            message="L4: Domain-validated credentials verified. Proceeding.",
            credential_ids=credential_ids,
        )

    def _validate_email_domain(self, email: str, required_domain: str) -> bool:
        """Validate email domain matches required domain."""
        email_lower = email.lower()
        domain_lower = required_domain.lower().replace("*.", "")

        if email_lower.endswith(f"@{domain_lower}"):
            return True

        for name, pattern in self.DOMAIN_PATTERNS.items():
            if domain_lower in name or re.search(pattern, required_domain, re.I):
                if re.search(pattern, email_lower, re.I):
                    return True

        return False

    async def test_credential(
        self,
        credential: dict,
        test_url: str = None,
        method: str = "POST",
    ) -> CredentialTestResult:
        """Test if a credential works by attempting authentication."""
        cred_id = credential.get("id", "unknown")
        cred_type = credential.get("credential_type", "unknown")

        if cred_type == "api_key":
            return await self._test_api_key(credential, test_url, cred_id)

        elif cred_type == "user_pass":
            return await self._test_user_pass(credential, test_url, method, cred_id)

        elif cred_type == "session_token":
            return await self._test_session_token(credential, test_url, cred_id)

        else:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.INVALID,
                message=f"Unknown credential type: {cred_type}",
                can_authenticate=False,
            )

    async def _test_api_key(
        self, credential: dict, test_url: str, cred_id: str
    ) -> CredentialTestResult:
        """Test API key validity."""
        if not test_url:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.VALID,
                message="API key present (no test URL provided)",
                can_authenticate=True,
            )

        api_key = credential.get("api_key", "")
        if not api_key:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.INVALID,
                message="API key not found in credential",
                can_authenticate=False,
            )

        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await self.client.get(test_url, headers=headers)
            if response.status_code == 200:
                return CredentialTestResult(
                    credential_id=cred_id,
                    status=CredentialStatus.VALID,
                    message="API key is valid",
                    can_authenticate=True,
                    response_time_ms=response.elapsed.total_seconds() * 1000,
                )
            elif response.status_code == 401:
                return CredentialTestResult(
                    credential_id=cred_id,
                    status=CredentialStatus.INVALID,
                    message="API key rejected (401 Unauthorized)",
                    can_authenticate=False,
                )
            else:
                return CredentialTestResult(
                    credential_id=cred_id,
                    status=CredentialStatus.VALID,
                    message=f"API key accepted, got status {response.status_code}",
                    can_authenticate=True,
                    response_time_ms=response.elapsed.total_seconds() * 1000,
                )
        except httpx.HTTPStatusError as e:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.INVALID,
                message=f"HTTP error: {e}",
                can_authenticate=False,
            )
        except Exception as e:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.INVALID,
                message=f"Connection error: {e}",
                can_authenticate=False,
            )

    async def _test_user_pass(
        self,
        credential: dict,
        test_url: str,
        method: str,
        cred_id: str,
    ) -> CredentialTestResult:
        """Test username/password validity."""
        username = credential.get("username", "")
        password = credential.get("password", "")

        if not username or not password:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.INVALID,
                message="Username or password missing",
                can_authenticate=False,
            )

        if not test_url:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.VALID,
                message="Credentials present (no test URL provided)",
                can_authenticate=True,
            )

        try:
            data = {"username": username, "password": password}
            response = await self.client.request(
                method, test_url, data=data, timeout=30.0
            )

            if response.status_code == 200:
                return CredentialTestResult(
                    credential_id=cred_id,
                    status=CredentialStatus.VALID,
                    message="Login successful",
                    can_authenticate=True,
                    response_time_ms=response.elapsed.total_seconds() * 1000,
                )
            elif response.status_code in [401, 403]:
                return CredentialTestResult(
                    credential_id=cred_id,
                    status=CredentialStatus.INVALID,
                    message="Login failed (invalid credentials)",
                    can_authenticate=False,
                    response_time_ms=response.elapsed.total_seconds() * 1000,
                )
            else:
                return CredentialTestResult(
                    credential_id=cred_id,
                    status=CredentialStatus.VALID,
                    message=f"Got response {response.status_code}",
                    can_authenticate=True,
                    response_time_ms=response.elapsed.total_seconds() * 1000,
                )

        except Exception as e:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.INVALID,
                message=f"Connection error: {e}",
                can_authenticate=False,
            )

    async def _test_session_token(
        self, credential: dict, test_url: str, cred_id: str
    ) -> CredentialTestResult:
        """Test session token validity."""
        token = credential.get("token", "")
        if not token:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.INVALID,
                message="Token not found",
                can_authenticate=False,
            )

        if not test_url:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.VALID,
                message="Token present (no test URL provided)",
                can_authenticate=True,
            )

        try:
            headers = {"Cookie": f"session={token}"}
            response = await self.client.get(test_url, headers=headers)

            if response.status_code == 200:
                return CredentialTestResult(
                    credential_id=cred_id,
                    status=CredentialStatus.VALID,
                    message="Session valid",
                    can_authenticate=True,
                    response_time_ms=response.elapsed.total_seconds() * 1000,
                )
            else:
                return CredentialTestResult(
                    credential_id=cred_id,
                    status=CredentialStatus.INVALID,
                    message=f"Session invalid (status {response.status_code})",
                    can_authenticate=False,
                )

        except Exception as e:
            return CredentialTestResult(
                credential_id=cred_id,
                status=CredentialStatus.INVALID,
                message=f"Error: {e}",
                can_authenticate=False,
            )

    def check_expiry(self, credential: dict) -> CredentialStatus:
        """Check if credential is expired or near expiry."""
        expires_at = credential.get("expires_at")
        if not expires_at:
            return CredentialStatus.VALID

        try:
            exp_date = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            now = datetime.now(exp_date.tzinfo) if exp_date.tzinfo else datetime.now(timezone.utc)
            
            if exp_date.tzinfo is None:
                exp_date = exp_date.replace(tzinfo=timezone.utc)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)

            if now > exp_date:
                return CredentialStatus.EXPIRED

            from datetime import timedelta
            if exp_date - now < timedelta(days=7):
                return CredentialStatus.NEAR_EXPIRY

            return CredentialStatus.VALID

        except (ValueError, TypeError):
            return CredentialStatus.VALID
