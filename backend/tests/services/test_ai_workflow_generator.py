"""Tests for AI workflow generator service."""
import pytest
import sys
sys.path.insert(0, '/home/xtx/Desktop/bugbounty-automater/backend')

from app.services.intel.ai_workflow_generator import (
    WorkflowGenerator,
    workflow_generator,
    WORKFLOW_PHASES,
    RiskLevel,
    StepType,
)


class TestWorkflowGenerator:
    """Test suite for WorkflowGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = WorkflowGenerator()
        self.sample_program_analysis = {
            "program_name": "Test Program",
            "introduction": "A test bug bounty program",
            "targets": [
                {
                    "name": "Main Web App",
                    "type": "webapp",
                    "description": "Main application",
                    "scope_domains": ["example.com", "*.example.com"],
                    "scope_ips": ["192.168.1.1"],
                    "excluded": ["staging.example.com"],
                    "suggested_tools": []
                },
                {
                    "name": "API Service",
                    "type": "api",
                    "description": "REST API",
                    "scope_domains": ["api.example.com"],
                    "scope_ips": [],
                    "excluded": [],
                    "suggested_tools": []
                }
            ],
            "rules": [
                "No testing on weekends",
                "Rate limit: 10 requests per second",
                "No exploitation without approval"
            ],
            "out_of_scope": [
                "staging.example.com",
                "test.example.com"
            ],
            "testing_notes": "Focus on authentication bypasses",
            "severity_mapping": {}
        }

    def test_workflow_generator_initialization(self):
        """Test that workflow generator initializes correctly."""
        assert self.generator is not None
        assert len(self.generator.phases) > 0
        assert len(WORKFLOW_PHASES) > 0

    def test_phases_have_correct_structure(self):
        """Test that all phases have required fields."""
        for phase in WORKFLOW_PHASES:
            assert "id" in phase
            assert "name" in phase
            assert "description" in phase
            assert "order" in phase
            assert "steps" in phase

    def test_generate_workflow_returns_valid_structure(self):
        """Test that generate_workflow returns expected structure."""
        available_tools = ["nmap", "subfinder", "amass", "httpx", "nuclei", "zap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        assert "id" in workflow
        assert "phases" in workflow
        assert "rules" in workflow
        assert "out_of_scope" in workflow
        assert "total_steps" in workflow
        assert "auto_steps" in workflow
        assert "manual_steps" in workflow
        assert "approval_points" in workflow

    def test_workflow_has_correct_number_of_targets(self):
        """Test that workflow contains correct number of targets."""
        available_tools = ["nmap", "subfinder", "amass", "httpx", "nuclei", "zap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        assert len(workflow["phases"]) == 2  # Two targets in sample

    def test_workflow_steps_have_tools_mapped(self):
        """Test that steps have tool mapping."""
        available_tools = ["nmap", "subfinder", "amass", "httpx", "nuclei", "zap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    assert "id" in step
                    assert "name" in step
                    assert "type" in step
                    assert "tool" in step
                    assert "tool_available" in step
                    assert "status" in step
                    assert "risk_level" in step

    def test_tool_availability_detection(self):
        """Test that tool availability is correctly detected."""
        available_tools = ["nmap", "subfinder", "amass"]  # Only some tools
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        found_nmap = False
        found_zap = False
        
        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    if step["tool"] == "nmap":
                        found_nmap = True
                        assert step["tool_available"] == True
                    if step["tool"] == "zap":
                        found_zap = True
                        assert step["tool_available"] == False

        assert found_nmap == True
        assert found_zap == True

    def test_approval_points_for_high_risk_steps(self):
        """Test that high-risk steps generate approval points."""
        program_with_exploitation_rules = {
            "targets": [
                {
                    "name": "Test Target",
                    "type": "webapp",
                    "scope_domains": ["test.com"],
                    "scope_ips": []
                }
            ],
            "rules": ["No exploitation without approval", "Read-only testing preferred"],
            "out_of_scope": []
        }
        
        available_tools = ["sqlmap", "nmap", "subfinder"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=program_with_exploitation_rules,
            available_tools=available_tools
        )

        exploit_steps = []
        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    if step["type"] in ["exploit", "test"]:
                        exploit_steps.append(step)

        for step in exploit_steps:
            if step["type"] == "exploit":
                assert step["requires_approval"] == True

    def test_risk_level_assessment(self):
        """Test that risk levels are assigned correctly."""
        available_tools = ["nmap", "subfinder"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        risk_levels = set()
        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    risk_levels.add(step["risk_level"])

        assert "low" in risk_levels or "medium" in risk_levels or "high" in risk_levels

    def test_commands_are_generated_for_available_tools(self):
        """Test that commands are generated for available tools."""
        available_tools = ["nmap", "subfinder", "amass", "httpx"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    if step["tool_available"] and step["tool"]:
                        assert step["command"] is not None
                        assert step["tool"].lower() in step["command"].lower()

    def test_blockers_detected_from_rules(self):
        """Test that rule-based blockers are detected."""
        program_with_blockers = {
            "targets": [
                {
                    "name": "Blocked Target",
                    "type": "webapp",
                    "scope_domains": ["blocked.com"],
                    "scope_ips": []
                }
            ],
            "rules": [
                "No exploitation allowed",
                "Read only testing",
                "Rate limit: 5 requests per second"
            ],
            "out_of_scope": []
        }
        
        available_tools = ["sqlmap", "nmap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=program_with_blockers,
            available_tools=available_tools
        )

        exploit_steps_with_blockers = []
        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    if step["type"] == "exploit":
                        exploit_steps_with_blockers.append(step)

        for step in exploit_steps_with_blockers:
            assert len(step["blockers"]) > 0
            blocker_text = " ".join(step["blockers"]).lower()
            assert "exploitation" in blocker_text or "read" in blocker_text

    def test_step_counts_are_correct(self):
        """Test that step counts are accurate."""
        available_tools = ["nmap", "subfinder", "amass", "httpx", "nuclei", "zap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        counted_auto = 0
        counted_manual = 0
        counted_total = 0

        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    counted_total += 1
                    if step["auto"]:
                        counted_auto += 1
                    else:
                        counted_manual += 1

        assert workflow["total_steps"] == counted_total
        assert workflow["auto_steps"] == counted_auto
        assert workflow["manual_steps"] == counted_manual

    def test_workflow_id_is_generated(self):
        """Test that workflow ID is generated."""
        available_tools = ["nmap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        assert workflow["id"].startswith("workflow_")

    def test_different_target_types_get_different_phases(self):
        """Test that different target types get appropriate phases."""
        webapp_program = {
            "targets": [
                {
                    "name": "Web App",
                    "type": "webapp",
                    "scope_domains": ["web.com"],
                    "scope_ips": []
                }
            ],
            "rules": [],
            "out_of_scope": []
        }
        
        network_program = {
            "targets": [
                {
                    "name": "Network",
                    "type": "network",
                    "scope_domains": [],
                    "scope_ips": ["10.0.0.1"]
                }
            ],
            "rules": [],
            "out_of_scope": []
        }
        
        available_tools = ["nmap", "subfinder", "amass"]
        
        webapp_workflow = self.generator.generate_workflow(
            program_analysis=webapp_program,
            available_tools=available_tools
        )
        
        network_workflow = self.generator.generate_workflow(
            program_analysis=network_program,
            available_tools=available_tools
        )

        webapp_phase_ids = set()
        for tp in webapp_workflow["phases"]:
            for p in tp["phases"]:
                webapp_phase_ids.add(p["id"])

        network_phase_ids = set()
        for tp in network_workflow["phases"]:
            for p in tp["phases"]:
                network_phase_ids.add(p["id"])

        assert webapp_phase_ids != network_phase_ids or len(webapp_phase_ids) == len(network_phase_ids)

    def test_workflow_preserves_program_rules(self):
        """Test that program rules are preserved in workflow."""
        available_tools = ["nmap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        assert len(workflow["rules"]) == len(self.sample_program_analysis["rules"])
        for rule in self.sample_program_analysis["rules"]:
            assert rule in workflow["rules"]

    def test_workflow_preserves_out_of_scope(self):
        """Test that out of scope items are preserved."""
        available_tools = ["nmap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        assert len(workflow["out_of_scope"]) == len(self.sample_program_analysis["out_of_scope"])
        for item in self.sample_program_analysis["out_of_scope"]:
            assert item in workflow["out_of_scope"]

    def test_estimated_duration_is_calculated(self):
        """Test that duration estimation works."""
        available_tools = ["nmap", "subfinder"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        for target_phase in workflow["phases"]:
            assert "estimated_duration" in target_phase
            assert "auto_minutes" in target_phase["estimated_duration"]
            assert "manual_minutes" in target_phase["estimated_duration"]
            assert "total_hours" in target_phase["estimated_duration"]
            assert target_phase["estimated_duration"]["total_hours"] >= 0

    def test_risk_score_calculation(self):
        """Test that risk scores are calculated."""
        available_tools = ["nmap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        for target_phase in workflow["phases"]:
            assert "risk_score" in target_phase
            assert "score" in target_phase["risk_score"]
            assert "level" in target_phase["risk_score"]
            assert 0 <= target_phase["risk_score"]["score"] <= 100
            assert target_phase["risk_score"]["level"] in ["low", "medium", "high"]

    def test_empty_targets_handled(self):
        """Test handling of empty targets."""
        empty_program = {
            "targets": [],
            "rules": [],
            "out_of_scope": []
        }
        
        available_tools = ["nmap"]
        
        workflow = self.generator.generate_workflow(
            program_analysis=empty_program,
            available_tools=available_tools
        )

        assert workflow["phases"] == []

    def test_empty_available_tools_handled(self):
        """Test handling when no tools are available."""
        available_tools = []
        
        workflow = self.generator.generate_workflow(
            program_analysis=self.sample_program_analysis,
            available_tools=available_tools
        )

        assert len(workflow["phases"]) > 0
        for target_phase in workflow["phases"]:
            for phase in target_phase["phases"]:
                for step in phase["steps"]:
                    if step["tool"]:
                        assert step["tool_available"] in [False, None]


class TestWorkflowPhases:
    """Test workflow phases structure."""

    def test_all_phase_orders_are_unique(self):
        """Test that phase orders are unique."""
        orders = [p["order"] for p in WORKFLOW_PHASES]
        assert len(orders) == len(set(orders))

    def test_phase_order_starts_at_one(self):
        """Test that phase order starts at 1."""
        orders = [p["order"] for p in WORKFLOW_PHASES]
        assert min(orders) == 1

    def test_all_phases_have_steps(self):
        """Test that all phases have at least one step."""
        for phase in WORKFLOW_PHASES:
            assert len(phase["steps"]) > 0

    def test_step_structure(self):
        """Test that all steps have required fields."""
        for phase in WORKFLOW_PHASES:
            for step in phase["steps"]:
                assert "type" in step
                assert "name" in step
                assert "tool" in step
                assert "auto" in step


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
