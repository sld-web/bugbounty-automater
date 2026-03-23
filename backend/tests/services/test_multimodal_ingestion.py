"""Tests for Multimodal Ingestion service."""
import pytest
import sys
sys.path.insert(0, '/home/xtx/Desktop/bugbounty-automater/backend')

from app.services.multimodal_ingestion import MultimodalIngestion


class TestMultimodalIngestion:
    """Test suite for MultimodalIngestion."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ingestion = MultimodalIngestion()

    def test_initialization(self):
        """Test service initialization."""
        assert self.ingestion is not None
        assert self.ingestion.openai_service is None

    def test_merge_findings(self):
        """Test merging findings from different analyses."""
        combined = {
            "domains": ["example.com"],
            "ips": ["1.2.3.4"],
            "technologies": ["nginx"],
            "auth_methods": [],
            "endpoints": [],
            "credentials": [],
            "attack_vectors": [],
            "architecture": []
        }

        new_findings = {
            "domains": ["test.com", "example.com"],
            "ips": ["5.6.7.8"],
            "technologies": ["apache"],
            "auth_methods": ["OAuth"],
            "endpoints": ["/api/users"],
            "credentials": ["admin:password"],
            "attack_vectors": ["XSS"],
            "architecture": ["microservices"]
        }

        self.ingestion._merge_findings(combined, new_findings)

        assert "example.com" in combined["domains"]
        assert "test.com" in combined["domains"]
        assert len(combined["domains"]) == 2
        assert "1.2.3.4" in combined["ips"]
        assert "5.6.7.8" in combined["ips"]
        assert "nginx" in combined["technologies"]
        assert "apache" in combined["technologies"]
        assert "OAuth" in combined["auth_methods"]
        assert "/api/users" in combined["endpoints"]
        assert "admin:password" in combined["credentials"]

    def test_merge_findings_with_lists(self):
        """Test merging findings with list values."""
        combined = {
            "domains": [],
            "ips": [],
            "technologies": [],
            "auth_methods": [],
            "endpoints": [],
            "credentials": [],
            "attack_vectors": [],
            "architecture": []
        }

        new_findings = {
            "domains": ["a.com", "b.com"],
            "technologies": ["nodejs"]
        }

        self.ingestion._merge_findings(combined, new_findings)

        assert len(combined["domains"]) == 2
        assert len(combined["technologies"]) == 1

    def test_merge_findings_empty_new(self):
        """Test merging with empty findings."""
        combined = {
            "domains": ["example.com"],
            "ips": [],
            "technologies": [],
            "auth_methods": [],
            "endpoints": [],
            "credentials": [],
            "attack_vectors": [],
            "architecture": []
        }

        self.ingestion._merge_findings(combined, {})

        assert combined["domains"] == ["example.com"]

    def test_merge_findings_string_values(self):
        """Test merging string values into list."""
        combined = {
            "domains": [],
            "ips": [],
            "technologies": [],
            "auth_methods": [],
            "endpoints": [],
            "credentials": [],
            "attack_vectors": [],
            "architecture": []
        }

        new_findings = {
            "domains": "single_domain.com"
        }

        self.ingestion._merge_findings(combined, new_findings)

        assert "single_domain.com" in combined["domains"]


class TestVisionAnalysis:
    """Test vision analysis functionality."""

    @pytest.mark.asyncio
    async def test_image_size_limit(self):
        """Test that large images are rejected."""
        ingestion = MultimodalIngestion()
        
        large_image = b"x" * (25 * 1024 * 1024)
        
        result = await ingestion.analyze_with_vision(large_image)
        
        assert "error" in result
        assert "too large" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_pdf_with_empty_bytes(self):
        """Test PDF analysis with empty bytes."""
        ingestion = MultimodalIngestion()
        
        result = await ingestion.analyze_pdf_with_vision(b"")
        
        assert "error" in result


class TestIntegration:
    """Integration tests for multimodal ingestion."""

    def test_complete_workflow(self):
        """Test complete ingestion workflow."""
        ingestion = MultimodalIngestion()
        
        findings = {
            "domains": ["example.com"],
            "ips": ["1.2.3.4"],
            "technologies": ["WordPress"],
            "auth_methods": ["JWT"],
            "endpoints": ["/api/v1/users"],
            "credentials": [],
            "attack_vectors": ["SQLi"],
            "architecture": []
        }
        
        ingestion._merge_findings(
            {"domains": [], "ips": [], "technologies": [], "auth_methods": [], 
             "endpoints": [], "credentials": [], "attack_vectors": [], "architecture": []},
            findings
        )
        
        assert len(findings["domains"]) > 0
        assert len(findings["technologies"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
