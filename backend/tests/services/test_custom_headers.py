"""Tests for custom headers service."""
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.custom_headers_service import CustomHeadersService, get_headers_service


class TestCustomHeadersService:
    """Tests for custom headers service."""

    @pytest.fixture
    def service(self):
        """Create fresh service instance."""
        service = CustomHeadersService()
        service._headers.clear()
        return service

    def test_add_header(self, service):
        """Test adding a header."""
        service.add_header("X-API-Key", "secret-key")
        
        header = service.get_header("X-API-Key")
        assert header.value == "secret-key"

    def test_add_header_case_insensitive(self, service):
        """Test header names are case-insensitive."""
        service.add_header("X-API-Key", "secret")
        
        assert service.get_header("x-api-key").value == "secret"
        assert service.get_header("X-API-KEY").value == "secret"

    def test_remove_header(self, service):
        """Test removing a header."""
        service.add_header("X-Test", "value")
        result = service.remove_header("X-Test")
        
        assert result is True
        assert service.get_header("X-Test") is None

    def test_remove_nonexistent_header(self, service):
        """Test removing non-existent header returns False."""
        result = service.remove_header("X-Does-Not-Exist")
        
        assert result is False

    def test_get_all_headers(self, service):
        """Test getting all headers."""
        service.add_header("X-Header1", "value1")
        service.add_header("X-Header2", "value2")
        
        headers = service.get_all_headers()
        
        assert len(headers) == 2
        assert headers["X-Header1"] == "value1"
        assert headers["X-Header2"] == "value2"

    def test_clear_headers(self, service):
        """Test clearing all headers."""
        service.add_header("X-Header1", "value1")
        service.add_header("X-Header2", "value2")
        
        count = service.clear_headers()
        
        assert count == 2
        assert len(service.get_all_headers()) == 0

    def test_clear_headers_by_source(self, service):
        """Test clearing headers by source."""
        service.add_header("X-Header1", "value1", source="policy")
        service.add_header("X-Header2", "value2", source="credential")
        
        count = service.clear_headers(source="policy")
        
        assert count == 1
        assert service.get_header("X-Header1") is None
        assert service.get_header("X-Header2").value == "value2"

    def test_get_headers_by_source(self, service):
        """Test filtering headers by source."""
        service.add_header("X-Policy", "policy-val", source="policy")
        service.add_header("X-Cred", "cred-val", source="credential")
        
        policy_headers = service.get_headers_by_source("policy")
        
        assert len(policy_headers) == 1
        assert "X-Policy" in policy_headers

    def test_inject_authentication_headers_api_key(self, service):
        """Test generating auth headers for API key credential."""
        headers = service.inject_authentication_headers(
            credential_type="api_key",
            credential_data={"api_key": "my-secret-key"},
            program_config={"api_key_header": "X-API-Key"}
        )
        
        assert headers["X-API-Key"] == "my-secret-key"

    def test_inject_authentication_headers_session_token(self, service):
        """Test generating auth headers for session token."""
        headers = service.inject_authentication_headers(
            credential_type="session_token",
            credential_data={"token": "abc123"},
        )
        
        assert headers["Authorization"] == "Bearer abc123"

    def test_inject_authentication_headers_user_pass_custom_headers(self, service):
        """Test generating auth headers for user/pass with custom headers."""
        headers = service.inject_authentication_headers(
            credential_type="user_pass",
            credential_data={"username": "testuser"},
            program_config={
                "custom_headers": {
                    "X-Username": "{username}"
                }
            }
        )
        
        assert headers["X-Username"] == "testuser"

    def test_resolve_header_template(self, service):
        """Test template resolution in header values."""
        resolved = service._resolve_header_template(
            "HackerOne-{username}",
            {"username": "testuser"}
        )
        
        assert resolved == "HackerOne-testuser"

    def test_get_injection_config(self, service):
        """Test getting injection configuration."""
        service.add_header("X-Header1", "val1", source="policy")
        service.add_header("X-Header2", "val2", source="credential")
        
        config = service.get_injection_config()
        
        assert config["total_count"] == 2
        assert "policy" in config["by_source"]
        assert "credential" in config["by_source"]


class TestSingletonBehavior:
    """Tests for singleton behavior."""

    def test_get_headers_service_returns_singleton(self):
        """Test that get_headers_service returns same instance."""
        service1 = get_headers_service()
        service2 = get_headers_service()
        
        assert service1 is service2
