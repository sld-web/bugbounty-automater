"""Credential Decision Engine API endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.credential_engine import (
    AuthLevel,
    CredentialDecision,
    CredentialDecisionEngine,
    CredentialStatus,
)
from app.models.credential import Credential

router = APIRouter(prefix="/auth-levels", tags=["credential-engine"])


class DecisionRequest(BaseModel):
    auth_level: str
    credentials: list[dict] = []
    program_domain: Optional[str] = None
    user_email: Optional[str] = None


class TestCredentialRequest(BaseModel):
    credential: dict
    test_url: Optional[str] = None
    method: str = "POST"


class CredentialDecisionResponse(BaseModel):
    level: str
    can_proceed: bool
    requires_credentials: bool
    message: str
    credential_ids: list[str]
    missing_info: list[str]
    approval_required: bool


class TestResultResponse(BaseModel):
    credential_id: str
    status: str
    message: str
    can_authenticate: bool
    response_time_ms: Optional[float]


class ExpiryCheckRequest(BaseModel):
    credentials: list[dict]


class ExpiryCheckResponse(BaseModel):
    results: list[dict]


@router.post("/decision")
async def get_credential_decision(request: DecisionRequest) -> CredentialDecisionResponse:
    """Get credential decision based on auth level and available credentials."""
    engine = CredentialDecisionEngine()

    decision = engine.get_decision(
        auth_level=request.auth_level,
        credentials=request.credentials,
        program_domain=request.program_domain,
        user_email=request.user_email,
    )

    return CredentialDecisionResponse(
        level=decision.level.value,
        can_proceed=decision.can_proceed,
        requires_credentials=decision.requires_credentials,
        message=decision.message,
        credential_ids=decision.credential_ids or [],
        missing_info=decision.missing_info or [],
        approval_required=decision.approval_required,
    )


@router.get("/decision/{auth_level}")
async def get_decision_for_level(
    auth_level: str,
    credentials: str = Query("[]"),
    program_domain: Optional[str] = None,
    user_email: Optional[str] = None,
) -> CredentialDecisionResponse:
    """Get credential decision with credentials as JSON string."""
    import json

    try:
        creds = json.loads(credentials)
    except json.JSONDecodeError:
        creds = []

    engine = CredentialDecisionEngine()

    decision = engine.get_decision(
        auth_level=auth_level,
        credentials=creds,
        program_domain=program_domain,
        user_email=user_email,
    )

    return CredentialDecisionResponse(
        level=decision.level.value,
        can_proceed=decision.can_proceed,
        requires_credentials=decision.requires_credentials,
        message=decision.message,
        credential_ids=decision.credential_ids or [],
        missing_info=decision.missing_info or [],
        approval_required=decision.approval_required,
    )


@router.post("/test")
async def test_credential(request: TestCredentialRequest) -> TestResultResponse:
    """Test if a credential is valid by attempting authentication."""
    engine = CredentialDecisionEngine()

    try:
        result = await engine.test_credential(
            credential=request.credential,
            test_url=request.test_url,
            method=request.method,
        )

        return TestResultResponse(
            credential_id=result.credential_id,
            status=result.status.value,
            message=result.message,
            can_authenticate=result.can_authenticate,
            response_time_ms=result.response_time_ms,
        )
    finally:
        await engine.close()


@router.post("/check-expiry")
async def check_credentials_expiry(request: ExpiryCheckRequest) -> ExpiryCheckResponse:
    """Check expiry status of multiple credentials."""
    engine = CredentialDecisionEngine()

    results = []
    for cred in request.credentials:
        status = engine.check_expiry(cred)
        cred_id = cred.get("id", "unknown")
        expires_at = cred.get("expires_at")

        results.append({
            "credential_id": cred_id,
            "status": status.value,
            "expires_at": expires_at,
            "is_expired": status == CredentialStatus.EXPIRED,
            "near_expiry": status == CredentialStatus.NEAR_EXPIRY,
        })

    return ExpiryCheckResponse(results=results)


@router.get("/validate-domain")
async def validate_email_domain(
    email: str = Query(..., description="Email to validate"),
    required_domain: str = Query(..., description="Required domain pattern"),
) -> dict:
    """Validate if an email matches a required domain."""
    engine = CredentialDecisionEngine()

    is_valid = engine._validate_email_domain(email, required_domain)

    return {
        "email": email,
        "required_domain": required_domain,
        "is_valid": is_valid,
        "message": (
            "Email domain matches requirement"
            if is_valid
            else f"Email must be from {required_domain} domain"
        ),
    }


@router.get("/levels")
async def list_auth_levels() -> dict:
    """List available authentication levels."""
    return {
        "levels": [
            {
                "level": "none",
                "name": "L0 - No Authentication",
                "description": "Public testing only, no credentials required",
                "requires_credentials": False,
            },
            {
                "level": "optional",
                "name": "L1 - Optional Authentication",
                "description": "Testing can proceed with or without credentials",
                "requires_credentials": False,
            },
            {
                "level": "required",
                "name": "L2 - Required Authentication",
                "description": "Valid credentials required to proceed",
                "requires_credentials": True,
            },
            {
                "level": "program_provided",
                "name": "L3 - Program-Provided Account",
                "description": "Must use account provided by the bug bounty program",
                "requires_credentials": True,
                "approval_required": True,
            },
            {
                "level": "domain_validated",
                "name": "L4 - Domain-Validated",
                "description": "Email must be from program's domain to register",
                "requires_credentials": True,
            },
        ]
    }


@router.post("/validate")
async def validate_credential(request: TestCredentialRequest) -> dict:
    """Validate a credential without testing against a live endpoint."""
    engine = CredentialDecisionEngine()

    cred = request.credential
    cred_type = cred.get("credential_type", "unknown")
    cred_id = cred.get("id", "unknown")

    errors = []

    if cred_type == "api_key":
        if not cred.get("api_key"):
            errors.append("API key is empty")
    elif cred_type == "user_pass":
        if not cred.get("username"):
            errors.append("Username is empty")
        if not cred.get("password"):
            errors.append("Password is empty")
    elif cred_type == "session_token":
        if not cred.get("token"):
            errors.append("Token is empty")

    expiry_status = engine.check_expiry(cred)
    if expiry_status == CredentialStatus.EXPIRED:
        errors.append("Credential has expired")
    elif expiry_status == CredentialStatus.NEAR_EXPIRY:
        errors.append("Credential expires soon")

    return {
        "credential_id": cred_id,
        "credential_type": cred_type,
        "is_valid": len(errors) == 0,
        "errors": errors,
        "expiry_status": expiry_status.value,
        "can_be_used": len(errors) == 0,
    }


class CredentialPolicyRequest(BaseModel):
    requirement_level: str = "optional"
    allowed_domains: list[str] = []
    email_format: Optional[str] = None
    custom_headers: dict[str, str] = {}
    public_testing_allowed: bool = True
    provisioning: Optional[dict] = None
    min_account_age_days: int = 0


class ProgramCredentialRequest(BaseModel):
    program_id: str
    policy: CredentialPolicyRequest


@router.post("/policy")
async def set_credential_policy(request: CredentialPolicyRequest) -> dict:
    """Set default credential policy."""
    return {
        "policy": {
            "requirement_level": request.requirement_level,
            "allowed_domains": request.allowed_domains,
            "email_format": request.email_format,
            "custom_headers": request.custom_headers,
            "public_testing_allowed": request.public_testing_allowed,
            "provisioning": request.provisioning,
            "min_account_age_days": request.min_account_age_days,
        }
    }


@router.get("/policy/templates")
async def get_policy_templates() -> dict:
    """Get predefined credential policy templates."""
    return {
        "templates": [
            {
                "name": "No Authentication (L0)",
                "level": "none",
                "policy": {
                    "requirement_level": "none",
                    "allowed_domains": [],
                    "public_testing_allowed": True,
                },
            },
            {
                "name": "Optional Authentication (L1)",
                "level": "optional",
                "policy": {
                    "requirement_level": "optional",
                    "allowed_domains": [],
                    "public_testing_allowed": True,
                },
            },
            {
                "name": "Required Authentication (L2)",
                "level": "required",
                "policy": {
                    "requirement_level": "required",
                    "allowed_domains": [],
                    "public_testing_allowed": False,
                },
            },
            {
                "name": "HackerOne Style (@wearehackerone.com)",
                "level": "domain_validated",
                "policy": {
                    "requirement_level": "domain_validated",
                    "allowed_domains": ["wearehackerone.com"],
                    "email_format": "username+pp@domain",
                    "public_testing_allowed": False,
                },
            },
            {
                "name": "Program-Provided Accounts (L3)",
                "level": "program_provided",
                "policy": {
                    "requirement_level": "program_provided",
                    "allowed_domains": ["wearehackerone.com"],
                    "public_testing_allowed": False,
                    "provisioning": {
                        "available": True,
                        "contact": "program@example.com",
                        "auto_request": False,
                    },
                },
            },
            {
                "name": "PayPal Style (Custom Headers)",
                "level": "custom_headers",
                "policy": {
                    "requirement_level": "required",
                    "allowed_domains": [],
                    "custom_headers": {
                        "X-PP-BB": "HackerOne-{username}"
                    },
                    "public_testing_allowed": True,
                },
            },
        ]
    }


@router.get("/policy/email-template")
async def generate_email_template(
    program_name: str,
    target_scope: str,
    researcher_handle: str,
    contact_email: str,
) -> dict:
    """Generate email template for requesting test accounts."""
    return {
        "subject": f"Test Account Request - {program_name} Bug Bounty",
        "body": f"""Hi,

I'm a security researcher participating in the {program_name} bug bounty program through HackerOne.

My HackerOne handle: {researcher_handle}

I would like to request test accounts for testing the following scope:
{target_scope}

These accounts will help me perform thorough authenticated testing to identify security vulnerabilities that may not be detectable through public endpoints alone.

Please let me know if you need any additional information.

Thank you for your time.

Best regards,
{researcher_handle}
""",
        "metadata": {
            "program_name": program_name,
            "researcher_handle": researcher_handle,
            "contact_email": contact_email,
            "target_scope": target_scope,
        }
    }


@router.post("/policy/check-compliance")
async def check_credential_compliance(
    credential_email: str = Query(..., description="Email to check compliance"),
    policy: CredentialPolicyRequest = ...,
) -> dict:
    """Check if a credential complies with program policy."""
    engine = CredentialDecisionEngine()

    violations = []

    if policy.allowed_domains:
        domain_valid = False
        for domain in policy.allowed_domains:
            if engine._validate_email_domain(credential_email, domain):
                domain_valid = True
                break

        if not domain_valid:
            violations.append(
                f"Email must be from one of: {', '.join(policy.allowed_domains)}"
            )

    return {
        "email": credential_email,
        "compliant": len(violations) == 0,
        "violations": violations,
        "policy": policy.model_dump(),
    }
