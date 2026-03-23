"""Tests for the Credential Decision Engine (L0-L4)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app
from app.services.credential_engine import (
    AuthLevel,
    CredentialDecisionEngine,
    CredentialStatus,
    CredentialDecision,
    CredentialTestResult,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def engine():
    """Create credential decision engine instance."""
    return CredentialDecisionEngine()


class TestL0NoAuthentication:
    """Tests for L0 - No Authentication (Public Testing Only)."""

    def test_l0_proceeds_without_credentials(self, engine):
        """L0 should proceed without any credentials."""
        decision = engine.get_decision(
            auth_level="none",
            credentials=[],
        )

        assert decision.can_proceed is True
        assert decision.requires_credentials is False
        assert decision.level == AuthLevel.L0_NONE
        assert "public" in decision.message.lower() or "proceeding" in decision.message.lower()

    def test_l0_ignores_credentials(self, engine):
        """L0 should work even if credentials are provided."""
        credentials = [
            {"id": "cred-1", "credential_type": "api_key", "api_key": "test-key"}
        ]

        decision = engine.get_decision(
            auth_level="none",
            credentials=credentials,
        )

        assert decision.can_proceed is True
        assert decision.level == AuthLevel.L0_NONE

    def test_l0_no_approval_required(self, engine):
        """L0 should not require approval."""
        decision = engine.get_decision(
            auth_level="none",
            credentials=[],
        )

        assert decision.approval_required is False

    def test_l0_api_endpoint(self, client):
        """Test L0 via API endpoint."""
        response = client.get("/api/auth-levels/decision/none")

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "none"
        assert data["can_proceed"] is True
        assert data["requires_credentials"] is False


class TestL1OptionalAuthentication:
    """Tests for L1 - Optional Authentication."""

    def test_l1_proceeds_without_credentials(self, engine):
        """L1 should proceed without credentials but prompt for them."""
        decision = engine.get_decision(
            auth_level="optional",
            credentials=[],
        )

        assert decision.can_proceed is True
        assert decision.requires_credentials is False
        assert decision.level == AuthLevel.L1_OPTIONAL

    def test_l1_uses_credentials_when_available(self, engine):
        """L1 should use provided credentials."""
        credentials = [
            {"id": "cred-1", "credential_type": "user_pass", "username": "test", "password": "pass"}
        ]

        decision = engine.get_decision(
            auth_level="optional",
            credentials=credentials,
        )

        assert decision.can_proceed is True
        assert len(decision.credential_ids) == 1
        assert decision.credential_ids[0] == "cred-1"

    def test_l1_no_approval_required(self, engine):
        """L1 should not require approval."""
        decision = engine.get_decision(
            auth_level="optional",
            credentials=[],
        )

        assert decision.approval_required is False

    def test_l1_api_endpoint(self, client):
        """Test L1 via API endpoint."""
        response = client.get("/api/auth-levels/decision/optional")

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "optional"
        assert data["can_proceed"] is True


class TestL2RequiredAuthentication:
    """Tests for L2 - Required Authentication."""

    def test_l2_requires_credentials(self, engine):
        """L2 should block without credentials."""
        decision = engine.get_decision(
            auth_level="required",
            credentials=[],
        )

        assert decision.can_proceed is False
        assert decision.requires_credentials is True
        assert len(decision.missing_info) > 0

    def test_l2_proceeds_with_valid_credentials(self, engine):
        """L2 should proceed with valid credentials."""
        credentials = [
            {"id": "cred-1", "credential_type": "api_key", "api_key": "valid-key"}
        ]

        decision = engine.get_decision(
            auth_level="required",
            credentials=credentials,
        )

        assert decision.can_proceed is True
        assert decision.requires_credentials is True
        assert len(decision.credential_ids) == 1

    def test_l2_blocks_with_expired_credentials(self, engine):
        """L2 should block with expired credentials."""
        credentials = [
            {"id": "cred-1", "credential_type": "api_key", "api_key": "key", "is_expired": True}
        ]

        decision = engine.get_decision(
            auth_level="required",
            credentials=credentials,
        )

        assert decision.can_proceed is False
        assert decision.missing_info == ["valid_credentials"]

    def test_l2_api_endpoint(self, client):
        """Test L2 via API endpoint."""
        response = client.get("/api/auth-levels/decision/required")

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "required"
        assert data["can_proceed"] is False


class TestL3ProgramProvidedAccount:
    """Tests for L3 - Program-Provided Account."""

    def test_l3_requires_approval(self, engine):
        """L3 should always require approval."""
        credentials = [
            {"id": "cred-1", "credential_type": "user_pass", "username": "program_user", "password": "pass"}
        ]

        decision = engine.get_decision(
            auth_level="program_provided",
            credentials=credentials,
        )

        assert decision.approval_required is True
        assert decision.requires_credentials is True

    def test_l3_blocks_without_credentials(self, engine):
        """L3 should block without credentials."""
        decision = engine.get_decision(
            auth_level="program_provided",
            credentials=[],
        )

        assert decision.can_proceed is False
        assert decision.approval_required is True

    def test_l3_api_endpoint(self, client):
        """Test L3 via API endpoint."""
        response = client.get("/api/auth-levels/decision/program_provided")

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "program_provided"
        assert data["approval_required"] is True


class TestL4DomainValidated:
    """Tests for L4 - Domain-Validated Email."""

    def test_l4_requires_domain_match(self, engine):
        """L4 should validate email domain."""
        credentials = [
            {"id": "cred-1", "credential_type": "user_pass", "username": "test@company.com", "password": "pass"}
        ]

        decision = engine.get_decision(
            auth_level="domain_validated",
            credentials=credentials,
            program_domain="company.com",
            user_email="test@company.com",
        )

        assert decision.can_proceed is True

    def test_l4_blocks_wrong_domain(self, engine):
        """L4 should block email from wrong domain."""
        credentials = [
            {"id": "cred-1", "credential_type": "user_pass", "username": "test@gmail.com", "password": "pass"}
        ]

        decision = engine.get_decision(
            auth_level="domain_validated",
            credentials=credentials,
            program_domain="company.com",
            user_email="test@gmail.com",
        )

        assert decision.can_proceed is False

    def test_l4_domain_validation_method(self, engine):
        """Test domain validation logic."""
        assert engine._validate_email_domain("user@company.com", "company.com") is True
        assert engine._validate_email_domain("user@sub.company.com", "company.com") is False
        assert engine._validate_email_domain("user@gmail.com", "company.com") is False

    def test_l4_api_endpoint(self, client):
        """Test L4 via API endpoint."""
        response = client.get("/api/auth-levels/decision/domain_validated")

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "domain_validated"


class TestCredentialExpiry:
    """Tests for credential expiry handling."""

    def test_check_expiry_valid(self, engine):
        """Test expiry check for valid credential."""
        cred = {"expires_at": (datetime.now() + timedelta(days=30)).isoformat()}
        status = engine.check_expiry(cred)
        assert status == CredentialStatus.VALID

    def test_check_expiry_expired(self, engine):
        """Test expiry check for expired credential."""
        cred = {"expires_at": (datetime.now() - timedelta(days=1)).isoformat()}
        status = engine.check_expiry(cred)
        assert status == CredentialStatus.EXPIRED

    def test_check_expiry_near_expiry(self, engine):
        """Test expiry check for near-expiry credential."""
        cred = {"expires_at": (datetime.now() + timedelta(days=5)).isoformat()}
        status = engine.check_expiry(cred)
        assert status == CredentialStatus.NEAR_EXPIRY

    def test_check_expiry_no_expiry(self, engine):
        """Test expiry check for credential without expiry."""
        cred = {}
        status = engine.check_expiry(cred)
        assert status == CredentialStatus.VALID

    def test_check_expiry_api(self, client):
        """Test expiry check via API."""
        credentials = [
            {"id": "test-1", "expires_at": (datetime.now() + timedelta(days=30)).isoformat()}
        ]
        response = client.post(
            "/api/auth-levels/check-expiry",
            json={"credentials": credentials}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["is_expired"] is False


class TestCredentialValidation:
    """Tests for credential validation via API."""

    def test_validate_api_key(self, client):
        """Test API key validation."""
        response = client.post(
            "/api/auth-levels/validate",
            json={"credential": {"id": "test-1", "credential_type": "api_key", "api_key": "valid-key"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_validate_missing_api_key(self, client):
        """Test API key validation with missing key."""
        response = client.post(
            "/api/auth-levels/validate",
            json={"credential": {"id": "test-1", "credential_type": "api_key"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0

    def test_validate_user_pass(self, client):
        """Test username/password validation."""
        response = client.post(
            "/api/auth-levels/validate",
            json={"credential": {"id": "test-1", "credential_type": "user_pass", "username": "user", "password": "pass"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_validate_missing_password(self, client):
        """Test validation with missing password."""
        response = client.post(
            "/api/auth-levels/validate",
            json={"credential": {"id": "test-1", "credential_type": "user_pass", "username": "user"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False


class TestPolicyTemplates:
    """Tests for credential policy templates."""

    def test_get_policy_templates(self, client):
        """Test getting policy templates."""
        response = client.get("/api/auth-levels/policy/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) >= 5

    def test_policy_template_l0(self, client):
        """Test L0 policy template."""
        response = client.get("/api/auth-levels/policy/templates")
        data = response.json()

        l0_template = next((t for t in data["templates"] if t["level"] == "none"), None)
        assert l0_template is not None
        assert l0_template["policy"]["public_testing_allowed"] is True

    def test_policy_template_hackerone_style(self, client):
        """Test HackerOne-style policy template."""
        response = client.get("/api/auth-levels/policy/templates")
        data = response.json()

        h1_template = next(
            (t for t in data["templates"] if "hackerone" in t["name"].lower()),
            None
        )
        assert h1_template is not None
        assert "wearehackerone.com" in h1_template["policy"]["allowed_domains"]


class TestEmailDomainValidation:
    """Tests for email domain validation API."""

    def test_validate_domain_valid(self, client):
        """Test valid domain validation."""
        response = client.get(
            "/api/auth-levels/validate-domain",
            params={"email": "user@company.com", "required_domain": "company.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_validate_domain_invalid(self, client):
        """Test invalid domain validation."""
        response = client.get(
            "/api/auth-levels/validate-domain",
            params={"email": "user@gmail.com", "required_domain": "company.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False


class TestComplianceChecking:
    """Tests for credential compliance checking."""

    def test_check_compliance_valid(self, client):
        """Test compliance check with valid credential."""
        response = client.post(
            "/api/auth-levels/policy/check-compliance",
            params={"credential_email": "user@company.com"},
            json={
                "allowed_domains": ["company.com"],
                "requirement_level": "domain_validated",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["compliant"] is True
        assert len(data["violations"]) == 0

    def test_check_compliance_invalid(self, client):
        """Test compliance check with invalid credential."""
        response = client.post(
            "/api/auth-levels/policy/check-compliance",
            params={"credential_email": "user@gmail.com"},
            json={
                "allowed_domains": ["company.com"],
                "requirement_level": "domain_validated",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["compliant"] is False
        assert len(data["violations"]) > 0


class TestMixedCredentialScenarios:
    """Tests for mixed credential scenarios."""

    def test_multiple_credentials(self, engine):
        """Test handling multiple credentials."""
        credentials = [
            {"id": "cred-1", "credential_type": "api_key", "api_key": "key1"},
            {"id": "cred-2", "credential_type": "user_pass", "username": "user", "password": "pass"},
        ]

        decision = engine.get_decision(
            auth_level="required",
            credentials=credentials,
        )

        assert decision.can_proceed is True
        assert len(decision.credential_ids) == 2

    def test_mixed_valid_and_expired(self, engine):
        """Test handling mix of valid and expired credentials."""
        credentials = [
            {"id": "cred-1", "credential_type": "api_key", "api_key": "valid", "expires_at": None},
            {"id": "cred-2", "credential_type": "api_key", "api_key": "expired", "expires_at": "2020-01-01"},
        ]

        decision = engine.get_decision(
            auth_level="required",
            credentials=credentials,
        )

        assert decision.can_proceed is True
        assert "cred-1" in decision.credential_ids

    def test_unknown_auth_level_defaults_to_none(self, engine):
        """Test handling unknown auth level."""
        decision = engine.get_decision(
            auth_level="unknown_level",
            credentials=[],
        )

        assert decision.can_proceed is True
        assert decision.level == AuthLevel.L0_NONE
