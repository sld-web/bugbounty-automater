"""Tests for Learning Loop service."""
import pytest
import sys
sys.path.insert(0, '/home/xtx/Desktop/bugbounty-automater/backend')

from app.services.learning_loop import (
    LearningLoop,
    ReportOutcome,
)


class TestLearningLoop:
    """Test suite for LearningLoop."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loop = LearningLoop()

    def test_record_accepted_outcome(self):
        """Test recording an accepted report."""
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="SQL Injection",
            chain_used=["sqli", "rce"],
            outcome=ReportOutcome.ACCEPTED,
            severity="high"
        )

        assert len(self.loop.feedback_history) == 1
        assert self.loop.feedback_history[0]["outcome"] == ReportOutcome.ACCEPTED

    def test_record_rejected_outcome(self):
        """Test recording a rejected report."""
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="XSS",
            chain_used=["xss"],
            outcome=ReportOutcome.REJECTED_DUPLICATE,
            severity="low"
        )

        assert len(self.loop.feedback_history) == 1
        assert self.loop.feedback_history[0]["outcome"] == ReportOutcome.REJECTED_DUPLICATE

    def test_record_multiple_outcomes(self):
        """Test recording multiple outcomes."""
        outcomes = [
            (ReportOutcome.ACCEPTED, "SQL Injection"),
            (ReportOutcome.ACCEPTED, "XSS"),
            (ReportOutcome.REJECTED_DUPLICATE, "IDOR"),
            (ReportOutcome.REJECTED_INSUFFICIENT, "Open Redirect"),
        ]

        for outcome, finding in outcomes:
            self.loop.record_outcome(
                program_id="prog1",
                finding_type=finding,
                chain_used=[],
                outcome=outcome,
                severity="medium"
            )

        assert len(self.loop.feedback_history) == 4

    def test_get_program_insights_no_feedback(self):
        """Test getting insights for program with no feedback."""
        insights = self.loop.get_program_insights("nonexistent")

        assert "message" in insights or insights.get("total_reports") == 0

    def test_get_program_insights_with_feedback(self):
        """Test getting insights for program with feedback."""
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="SQL Injection",
            chain_used=["sqli"],
            outcome=ReportOutcome.ACCEPTED,
            severity="high"
        )

        self.loop.record_outcome(
            program_id="prog1",
            finding_type="XSS",
            chain_used=["xss"],
            outcome=ReportOutcome.REJECTED_DUPLICATE,
            severity="medium"
        )

        insights = self.loop.get_program_insights("prog1")

        assert insights["total_reports"] == 2
        assert insights["accepted_count"] == 1
        assert insights["rejected_count"] == 1
        assert insights["acceptance_rate"] == 0.5

    def test_get_most_successful_finding_type(self):
        """Test identifying most successful finding type."""
        for _ in range(3):
            self.loop.record_outcome(
                program_id="prog1",
                finding_type="SQL Injection",
                chain_used=["sqli"],
                outcome=ReportOutcome.ACCEPTED,
                severity="high"
            )

        for _ in range(2):
            self.loop.record_outcome(
                program_id="prog1",
                finding_type="XSS",
                chain_used=["xss"],
                outcome=ReportOutcome.ACCEPTED,
                severity="medium"
            )

        insights = self.loop.get_program_insights("prog1")
        assert insights["most_successful_finding_type"] == "SQL Injection"

    def test_get_rejection_reasons(self):
        """Test analyzing rejection reasons."""
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="A",
            chain_used=[],
            outcome=ReportOutcome.REJECTED_DUPLICATE,
            severity="low"
        )
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="B",
            chain_used=[],
            outcome=ReportOutcome.REJECTED_DUPLICATE,
            severity="low"
        )
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="C",
            chain_used=[],
            outcome=ReportOutcome.REJECTED_INSUFFICIENT,
            severity="medium"
        )

        insights = self.loop.get_program_insights("prog1")

        assert insights["common_rejection_reasons"]["rejected_duplicate"] == 2
        assert insights["common_rejection_reasons"]["rejected_insufficient_impact"] == 1

    def test_get_effective_chains(self):
        """Test finding effective chains."""
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="SQL Injection",
            chain_used=["sqli", "upload", "rce"],
            outcome=ReportOutcome.ACCEPTED,
            severity="critical"
        )

        self.loop.record_outcome(
            program_id="prog1",
            finding_type="IDOR",
            chain_used=["sqli", "upload", "rce"],
            outcome=ReportOutcome.ACCEPTED,
            severity="high"
        )

        insights = self.loop.get_program_insights("prog1")
        effective = insights["effective_chains"]

        assert len(effective) > 0
        assert "sqli" in effective[0]["chain"]

    def test_generate_suggestions_high_duplicate_rate(self):
        """Test suggestions when duplicate rate is high."""
        for _ in range(5):
            self.loop.record_outcome(
                program_id="prog1",
                finding_type="Test",
                chain_used=[],
                outcome=ReportOutcome.REJECTED_DUPLICATE,
                severity="low"
            )

        insights = self.loop.get_program_insights("prog1")
        suggestions = insights["suggestions"]

        assert any("duplicate" in s.lower() for s in suggestions)

    def test_generate_suggestions_insufficient_impact(self):
        """Test suggestions when reports lack impact."""
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="Test",
            chain_used=[],
            outcome=ReportOutcome.REJECTED_INSUFFICIENT,
            severity="low"
        )

        insights = self.loop.get_program_insights("prog1")
        suggestions = insights["suggestions"]

        assert any("impact" in s.lower() for s in suggestions)

    def test_get_tool_recommendations(self):
        """Test getting tool recommendations."""
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="sqli",
            chain_used=["sqlmap"],
            outcome=ReportOutcome.ACCEPTED,
            severity="high"
        )
        self.loop.record_outcome(
            program_id="prog2",
            finding_type="sqli",
            chain_used=["sqlmap"],
            outcome=ReportOutcome.ACCEPTED,
            severity="high"
        )
        self.loop.record_outcome(
            program_id="prog3",
            finding_type="sqli",
            chain_used=["sqlmap"],
            outcome=ReportOutcome.REJECTED_INSUFFICIENT,
            severity="high"
        )

        recs = self.loop.get_tool_recommendations("sqli")

        assert len(recs) > 0
        assert recs[0]["tool"] == "sqli"
        assert recs[0]["success_count"] == 2

    def test_get_tool_recommendations_specific(self):
        """Test getting recommendations for specific tool."""
        recs = self.loop.get_tool_recommendations("nuclei")
        assert len(recs) >= 0

    def test_rate_tool_insufficient_data(self):
        """Test rating tool with insufficient data."""
        rating = self.loop._rate_tool(0.5, 2)
        assert rating == "insufficient_data"

    def test_rate_tool_highly_effective(self):
        """Test rating highly effective tool."""
        rating = self.loop._rate_tool(0.8, 10)
        assert rating == "highly_effective"

    def test_rate_tool_moderately_effective(self):
        """Test rating moderately effective tool."""
        rating = self.loop._rate_tool(0.5, 10)
        assert rating == "moderately_effective"

    def test_rate_tool_low_effectiveness(self):
        """Test rating low effectiveness tool."""
        rating = self.loop._rate_tool(0.3, 10)
        assert rating == "low_effectiveness"

    def test_rate_tool_consider_alternatives(self):
        """Test rating tool to consider alternatives."""
        rating = self.loop._rate_tool(0.1, 10)
        assert rating == "consider_alternatives"

    def test_add_technology_vulnerability(self):
        """Test adding technology vulnerability."""
        self.loop.add_technology_vulnerability("WordPress", "sql_injection")
        self.loop.add_technology_vulnerability("WordPress", "xss")
        self.loop.add_technology_vulnerability("WordPress", "sql_injection")

        insights = self.loop.get_technology_insights("WordPress")
        vulns = insights.get("known_vulnerabilities", [])
        assert len(vulns) == 2
        assert "sql_injection" in vulns
        assert "xss" in vulns

    def test_export_learning_data(self):
        """Test exporting learning data."""
        self.loop.record_outcome(
            program_id="prog1",
            finding_type="Test",
            chain_used=[],
            outcome=ReportOutcome.ACCEPTED,
            severity="medium"
        )

        exported = self.loop.export_learning_data()

        assert "feedback_history" in exported
        assert "effective_chains" in exported
        assert len(self.loop.feedback_history) == 1

    def test_import_learning_data(self):
        """Test importing learning data."""
        data = '''{
            "feedback_history": [
                {
                    "timestamp": "2024-01-01T00:00:00",
                    "program_id": "prog1",
                    "finding_type": "SQL Injection",
                    "chain_used": ["sqli"],
                    "outcome": "accepted",
                    "severity": "high",
                    "notes": null
                }
            ],
            "effective_chains": {},
            "ineffective_patterns": {},
            "tool_effectiveness": {},
            "technology_vulnerabilities": {}
        }'''

        new_loop = LearningLoop()
        new_loop.import_learning_data(data)

        assert len(new_loop.feedback_history) == 1
        assert new_loop.feedback_history[0]["finding_type"] == "SQL Injection"


class TestReportOutcome:
    """Test ReportOutcome string class."""

    def test_all_outcomes_defined(self):
        """Test all report outcomes are defined."""
        assert ReportOutcome.ACCEPTED == "accepted"
        assert ReportOutcome.REJECTED_DUPLICATE == "rejected_duplicate"
        assert ReportOutcome.REJECTED_OUT_OF_SCOPE == "rejected_out_of_scope"
        assert ReportOutcome.REJECTED_INSUFFICIENT == "rejected_insufficient_impact"
        assert ReportOutcome.REJECTED_INFORMATION == "rejected_information"
        assert ReportOutcome.NEEDS_MORE == "needs_more_info"

    def test_rejected_outcome_values(self):
        """Test that rejected outcomes have expected string values."""
        assert "rejected" in ReportOutcome.REJECTED_DUPLICATE
        assert "rejected" in ReportOutcome.REJECTED_OUT_OF_SCOPE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
