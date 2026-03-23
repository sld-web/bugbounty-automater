"""Tests for flows API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
import sys
sys.path.insert(0, '/home/xtx/Desktop/bugbounty-automater/backend')

from app.main import app


class TestFlowsAPI:
    """Test suite for flows API endpoints."""

    @pytest.fixture
    def sample_program_analysis(self):
        """Sample program analysis for testing."""
        return {
            "program_analysis": {
                "targets": [
                    {
                        "name": "Test Web App",
                        "type": "webapp",
                        "scope_domains": ["test.com", "*.test.com"],
                        "scope_ips": ["192.168.1.1"],
                        "excluded": ["staging.test.com"]
                    }
                ],
                "rules": [
                    "No exploitation without approval",
                    "Rate limit: 10 req/s",
                    "Focus on SQL injection"
                ],
                "out_of_scope": ["staging.test.com", "dev.test.com"],
                "testing_notes": "Test authentication flows",
                "severity_mapping": {
                    "critical": ["RCE", "SQLi"],
                    "high": ["XSS", "IDOR"]
                }
            }
        }

    @pytest.fixture
    def sample_workflow(self):
        """Sample workflow for execute-step testing."""
        return {
            "phases": [
                {
                    "target_id": "target_1",
                    "target_name": "Test Target",
                    "target_type": "webapp",
                    "domains": ["test.com"],
                    "ips": [],
                    "phases": [
                        {
                            "id": "test_recon",
                            "name": "Reconnaissance",
                            "steps": [
                                {
                                    "id": "step_recon_test",
                                    "type": "recon",
                                    "name": "Subdomain Enumeration",
                                    "tool": "subfinder",
                                    "tool_available": True,
                                    "auto": True,
                                    "status": "pending"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_generate_workflow_endpoint(self, sample_program_analysis):
        """Test POST /flows/generate endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/generate", json=sample_program_analysis)

        assert response.status_code == 200
        data = response.json()
        
        assert "workflow" in data
        assert "available_tools" in data
        assert "summary" in data
        
        workflow = data["workflow"]
        assert "phases" in workflow
        assert "rules" in workflow
        assert "out_of_scope" in workflow
        
        summary = data["summary"]
        assert "total_steps" in summary
        assert "auto_steps" in summary
        assert "manual_steps" in summary
        assert "approval_points" in summary

    @pytest.mark.asyncio
    async def test_generate_workflow_with_multiple_targets(self):
        """Test workflow generation with multiple targets."""
        multi_target_analysis = {
            "program_analysis": {
                "targets": [
                    {
                        "name": "Web App 1",
                        "type": "webapp",
                        "scope_domains": ["app1.com"],
                        "scope_ips": []
                    },
                    {
                        "name": "API",
                        "type": "api",
                        "scope_domains": ["api.com"],
                        "scope_ips": []
                    },
                    {
                        "name": "Mobile",
                        "type": "mobile",
                        "scope_domains": ["mobile.com"],
                        "scope_ips": []
                    }
                ],
                "rules": [],
                "out_of_scope": []
            }
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/generate", json=multi_target_analysis)

        assert response.status_code == 200
        data = response.json()
        
        assert len(data["workflow"]["phases"]) == 3

    @pytest.mark.asyncio
    async def test_generate_workflow_empty_targets(self):
        """Test workflow generation with no targets."""
        empty_analysis = {
            "program_analysis": {
                "targets": [],
                "rules": [],
                "out_of_scope": []
            }
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/generate", json=empty_analysis)

        assert response.status_code == 200
        data = response.json()
        
        assert len(data["workflow"]["phases"]) == 0

    @pytest.mark.asyncio
    async def test_execute_step_endpoint(self, sample_workflow):
        """Test POST /flows/execute-step endpoint."""
        execute_request = {
            "step_id": "step_recon_test",
            "workflow_data": sample_workflow,
            "target": "test.com",
            "params": {}
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/execute-step", json=execute_request)

        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["step_id"] == "step_recon_test"

    @pytest.mark.asyncio
    async def test_execute_step_manual_required(self):
        """Test execute-step when tool is not available."""
        workflow = {
            "phases": [
                {
                    "target_id": "target_1",
                    "phases": [
                        {
                            "id": "test_phase",
                            "steps": [
                                {
                                    "id": "manual_step",
                                    "type": "manual_review",
                                    "name": "Manual Test",
                                    "tool": None,
                                    "tool_available": False,
                                    "auto": False
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        execute_request = {
            "step_id": "manual_step",
            "workflow_data": workflow,
            "target": "test.com"
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/execute-step", json=execute_request)

        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "manual_required"

    @pytest.mark.asyncio
    async def test_execute_step_not_found(self):
        """Test execute-step with non-existent step."""
        workflow = {"phases": []}

        execute_request = {
            "step_id": "nonexistent_step",
            "workflow_data": workflow,
            "target": "test.com"
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/execute-step", json=execute_request)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_execute_step_tool_not_available(self):
        """Test execute-step when tool is not installed."""
        workflow = {
            "phases": [
                {
                    "target_id": "target_1",
                    "phases": [
                        {
                            "id": "test_phase",
                            "steps": [
                                {
                                    "id": "zap_step",
                                    "name": "ZAP Scan",
                                    "tool": "zap",
                                    "tool_available": False
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        execute_request = {
            "step_id": "zap_step",
            "workflow_data": workflow,
            "target": "test.com"
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/execute-step", json=execute_request)

        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "tool_not_available"

    @pytest.mark.asyncio
    async def test_approval_request_endpoint(self, sample_workflow):
        """Test POST /flows/approval-request endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/flows/approval-request",
                params={
                    "step_id": "test_step",
                    "target": "test.com",
                    "reason": "High risk operation"
                },
                json=sample_workflow
            )

        assert response.status_code == 200
        data = response.json()
        
        assert "request_id" in data
        assert data["step_id"] == "test_step"
        assert data["target"] == "test.com"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_workflow_contains_correct_phases(self, sample_program_analysis):
        """Test that generated workflow contains expected phases."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/generate", json=sample_program_analysis)

        assert response.status_code == 200
        data = response.json()
        
        workflow = data["workflow"]
        assert len(workflow["phases"]) > 0
        
        first_target = workflow["phases"][0]
        phase_names = [p["name"] for p in first_target["phases"]]
        
        expected_phases = ["Reconnaissance", "Enumeration", "Vulnerability Detection"]
        for expected in expected_phases:
            assert any(expected.lower() in name.lower() for name in phase_names)

    @pytest.mark.asyncio
    async def test_workflow_respects_program_rules(self):
        """Test that workflow respects program rules."""
        analysis_with_rules = {
            "program_analysis": {
                "targets": [
                    {
                        "name": "Restricted Target",
                        "type": "webapp",
                        "scope_domains": ["restricted.com"],
                        "scope_ips": []
                    }
                ],
                "rules": [
                    "No exploitation",
                    "Read only testing",
                    "Requires approval for all scans"
                ],
                "out_of_scope": []
            }
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/generate", json=analysis_with_rules)

        assert response.status_code == 200
        data = response.json()
        
        workflow = data["workflow"]
        assert len(workflow["rules"]) == 3
        
        approval_points = workflow["approval_points"]
        assert len(approval_points) > 0

    @pytest.mark.asyncio
    async def test_workflow_summary_accuracy(self):
        """Test that workflow summary is accurate."""
        analysis = {
            "program_analysis": {
                "targets": [
                    {
                        "name": "Test Target",
                        "type": "webapp",
                        "scope_domains": ["test.com"],
                        "scope_ips": []
                    }
                ],
                "rules": [],
                "out_of_scope": []
            }
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/generate", json=analysis)

        assert response.status_code == 200
        data = response.json()
        
        summary = data["summary"]
        workflow = data["workflow"]
        
        assert summary["total_targets"] == len(workflow["phases"])
        assert summary["total_steps"] == workflow["total_steps"]
        assert summary["auto_steps"] == workflow["auto_steps"]
        assert summary["manual_steps"] == workflow["manual_steps"]

    @pytest.mark.asyncio
    async def test_workflow_contains_tool_commands(self):
        """Test that workflow steps have commands for available tools."""
        analysis = {
            "program_analysis": {
                "targets": [
                    {
                        "name": "Test Target",
                        "type": "webapp",
                        "scope_domains": ["test.com"],
                        "scope_ips": []
                    }
                ],
                "rules": [],
                "out_of_scope": []
            }
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/flows/generate", json=analysis)

        assert response.status_code == 200
        data = response.json()
        
        workflow = data["workflow"]
        steps_with_commands = 0
        
        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    if step.get("tool_available") and step.get("tool"):
                        assert "command" in step
                        steps_with_commands += 1

        assert steps_with_commands > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
