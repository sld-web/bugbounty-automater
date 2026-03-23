"""Learning Loop service for continuous improvement from report outcomes."""
import json
import logging
from datetime import datetime
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReportOutcome(str):
    ACCEPTED = "accepted"
    REJECTED_DUPLICATE = "rejected_duplicate"
    REJECTED_OUT_OF_SCOPE = "rejected_out_of_scope"
    REJECTED_INSUFFICIENT = "rejected_insufficient_impact"
    REJECTED_INFORMATION = "rejected_information"
    NEEDS_MORE = "needs_more_info"


class LearningLoop:
    """Continuous learning system from bug bounty report outcomes."""

    def __init__(self):
        self.feedback_history: list[dict] = []
        self.effective_chains: dict[str, int] = defaultdict(int)
        self.ineffective_patterns: dict[str, int] = defaultdict(int)
        self.program_insights: dict[str, dict] = {}
        self.tool_effectiveness: dict[str, dict] = defaultdict(lambda: {"success": 0, "failure": 0})
        self.technology_vulnerabilities: dict[str, list[str]] = defaultdict(list)

    def record_outcome(
        self,
        program_id: str,
        finding_type: str,
        chain_used: list[str] | None,
        outcome: ReportOutcome,
        severity: str,
        notes: str | None = None
    ) -> None:
        """Record the outcome of a submitted report."""
        feedback = {
            "timestamp": datetime.utcnow().isoformat(),
            "program_id": program_id,
            "finding_type": finding_type,
            "chain_used": chain_used or [],
            "outcome": outcome,
            "severity": severity,
            "notes": notes
        }

        self.feedback_history.append(feedback)
        self._update_statistics(feedback)

        logger.info(f"Recorded feedback: {finding_type} -> {outcome}")

    def _update_statistics(self, feedback: dict) -> None:
        """Update internal statistics based on feedback."""
        outcome = feedback["outcome"]
        finding_type = feedback["finding_type"]
        chain = feedback["chain_used"]

        if outcome == ReportOutcome.ACCEPTED:
            if chain:
                for step in chain:
                    self.effective_chains[step] += 1
            self.tool_effectiveness[finding_type]["success"] += 1
        else:
            self.ineffective_patterns[finding_type] += 1
            self.tool_effectiveness[finding_type]["failure"] += 1

    def get_program_insights(self, program_id: str) -> dict:
        """Get insights learned for a specific program."""
        program_feedback = [
            f for f in self.feedback_history
            if f["program_id"] == program_id
        ]

        if not program_feedback:
            return {
                "message": "No feedback recorded for this program yet",
                "suggestions": []
            }

        accepted = [f for f in program_feedback if f["outcome"] == ReportOutcome.ACCEPTED]
        rejected = [f for f in program_feedback if f["outcome"] != ReportOutcome.ACCEPTED]

        insights = {
            "total_reports": len(program_feedback),
            "acceptance_rate": len(accepted) / len(program_feedback) if program_feedback else 0,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "most_successful_finding_type": self._get_most_successful(program_feedback),
            "common_rejection_reasons": self._get_rejection_reasons(program_feedback),
            "effective_chains": self._get_effective_chains(program_feedback),
            "suggestions": self._generate_suggestions(program_feedback)
        }

        return insights

    def _get_most_successful(self, feedback: list[dict]) -> str | None:
        """Find the most successful finding type."""
        accepted = [f for f in feedback if f["outcome"] == ReportOutcome.ACCEPTED]
        if not accepted:
            return None

        by_type = defaultdict(int)
        for f in accepted:
            by_type[f["finding_type"]] += 1

        return max(by_type, key=by_type.get)

    def _get_rejection_reasons(self, feedback: list[dict]) -> dict[str, int]:
        """Analyze common rejection reasons."""
        rejected = [f for f in feedback if f["outcome"] != ReportOutcome.ACCEPTED]
        reasons = defaultdict(int)

        for f in rejected:
            reasons[f["outcome"]] += 1

        return dict(reasons)

    def _get_effective_chains(self, feedback: list[dict]) -> list[dict]:
        """Find chains that led to accepted reports."""
        accepted_with_chains = [
            f for f in feedback
            if f["outcome"] == ReportOutcome.ACCEPTED and f["chain_used"]
        ]

        chain_counts = defaultdict(int)
        for f in accepted_with_chains:
            chain_key = " -> ".join(f["chain_used"])
            chain_counts[chain_key] += 1

        return [
            {"chain": chain, "success_count": count}
            for chain, count in sorted(chain_counts.items(), key=lambda x: -x[1])
        ][:10]

    def _generate_suggestions(self, feedback: list[dict]) -> list[str]:
        """Generate suggestions based on feedback patterns."""
        suggestions = []

        accepted = [f for f in feedback if f["outcome"] == ReportOutcome.ACCEPTED]
        rejected = [f for f in feedback if f["outcome"] != ReportOutcome.ACCEPTED]

        if rejected:
            duplicate_count = sum(
                1 for f in rejected
                if f["outcome"] == ReportOutcome.REJECTED_DUPLICATE
            )
            if duplicate_count > len(rejected) * 0.3:
                suggestions.append(
                    "High duplicate rate - verify findings aren't already known before submitting"
                )

            insufficient_count = sum(
                1 for f in rejected
                if f["outcome"] == ReportOutcome.REJECTED_INSUFFICIENT
            )
            if insufficient_count > 0:
                suggestions.append(
                    "Focus on demonstrating clearer business impact"
                )

        critical_accepted = [
            f for f in accepted
            if f["severity"] in ["critical", "high"]
        ]
        if critical_accepted:
            most_common = self._get_most_successful(critical_accepted)
            if most_common:
                suggestions.append(
                    f"High-severity findings of type '{most_common}' are successful - prioritize these"
                )

        return suggestions

    def get_tool_recommendations(self, finding_type: str | None = None) -> list[dict]:
        """Get tool recommendations based on effectiveness data."""
        recommendations = []

        if finding_type:
            tools = {finding_type: self.tool_effectiveness[finding_type]}
        else:
            tools = dict(self.tool_effectiveness)

        for tool, stats in tools.items():
            total = stats["success"] + stats["failure"]
            if total > 0:
                success_rate = stats["success"] / total
                recommendations.append({
                    "tool": tool,
                    "success_count": stats["success"],
                    "failure_count": stats["failure"],
                    "success_rate": success_rate,
                    "recommendation": self._rate_tool(success_rate, total)
                })

        return sorted(recommendations, key=lambda x: -x["success_rate"])

    def _rate_tool(self, success_rate: float, total: int) -> str:
        """Rate a tool based on its effectiveness."""
        if total < 3:
            return "insufficient_data"
        elif success_rate > 0.7:
            return "highly_effective"
        elif success_rate > 0.4:
            return "moderately_effective"
        elif success_rate > 0.2:
            return "low_effectiveness"
        else:
            return "consider_alternatives"

    def get_technology_insights(self, technology: str) -> dict:
        """Get insights about vulnerabilities in specific technology."""
        return {
            "technology": technology,
            "known_vulnerabilities": self.technology_vulnerabilities.get(technology, []),
            "common_chains": self._get_tech_chains(technology),
            "tips": self._get_tech_tips(technology)
        }

    def add_technology_vulnerability(self, technology: str, vuln_type: str) -> None:
        """Record a vulnerability found in a technology."""
        if vuln_type not in self.technology_vulnerabilities[technology]:
            self.technology_vulnerabilities[technology].append(vuln_type)

    def _get_tech_chains(self, technology: str) -> list[dict]:
        """Find effective chains for a technology."""
        relevant_feedback = [
            f for f in self.feedback_history
            if technology.lower() in str(f.get("chain_used", [])).lower()
        ]

        accepted = [f for f in relevant_feedback if f["outcome"] == ReportOutcome.ACCEPTED]
        return [
            {"chain": f["chain_used"], "finding_type": f["finding_type"]}
            for f in accepted
            if f["chain_used"]
        ][:5]

    def _get_tech_tips(self, technology: str) -> list[str]:
        """Generate tips for testing a technology."""
        tips = []

        known_vulns = self.technology_vulnerabilities.get(technology, [])
        if known_vulns:
            tips.append(f"Known vulnerability types: {', '.join(known_vulns)}")

        return tips if tips else ["No specific tips available yet"]

    def export_learning_data(self) -> str:
        """Export learning data as JSON."""
        return json.dumps({
            "feedback_history": self.feedback_history,
            "effective_chains": dict(self.effective_chains),
            "ineffective_patterns": dict(self.ineffective_patterns),
            "tool_effectiveness": dict(self.tool_effectiveness),
            "technology_vulnerabilities": dict(self.technology_vulnerabilities),
            "exported_at": datetime.utcnow().isoformat()
        }, indent=2)

    def import_learning_data(self, data: str) -> None:
        """Import learning data from JSON."""
        try:
            parsed = json.loads(data)

            self.feedback_history = parsed.get("feedback_history", [])
            self.effective_chains = defaultdict(int, parsed.get("effective_chains", {}))
            self.ineffective_patterns = defaultdict(int, parsed.get("ineffective_patterns", {}))
            self.tool_effectiveness = defaultdict(
                lambda: {"success": 0, "failure": 0},
                parsed.get("tool_effectiveness", {})
            )
            self.technology_vulnerabilities = defaultdict(
                list,
                parsed.get("technology_vulnerabilities", {})
            )

            logger.info("Learning data imported successfully")

        except Exception as e:
            logger.error(f"Failed to import learning data: {e}")


learning_loop = LearningLoop()
