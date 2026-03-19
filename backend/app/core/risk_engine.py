"""Risk scoring engine for determining action approval requirements."""
from dataclasses import dataclass

from app.models.approval import RiskLevel
from app.models.plugin_run import PermissionLevel


@dataclass
class RiskAssessment:
    score: float
    level: RiskLevel
    factors: dict
    requires_approval: bool
    auto_approve: bool


class RiskEngine:
    """Calculate risk scores for actions and determine approval requirements."""

    SCORE_THRESHOLDS = {
        RiskLevel.LOW: 25,
        RiskLevel.MEDIUM: 50,
        RiskLevel.HIGH: 75,
    }

    AUTO_APPROVE_THRESHOLD = 20

    def __init__(self):
        self.weights = {
            "data_sensitivity": 0.25,
            "financial_impact": 0.20,
            "scope_violation_risk": 0.30,
            "action_type": 0.25,
        }

    def assess(
        self,
        action_type: str,
        target: str,
        plugin_permission: PermissionLevel,
        data_sensitivity: float = 0.5,
        scope_info: dict | None = None,
        evidence: dict | None = None,
    ) -> RiskAssessment:
        """Assess the risk of an action."""
        factors = {}

        action_score = self._score_action_type(action_type, plugin_permission)
        factors["action_type"] = action_score

        scope_score = self._score_scope_risk(target, scope_info)
        factors["scope_risk"] = scope_score

        sensitivity_score = data_sensitivity * 100
        factors["data_sensitivity"] = sensitivity_score

        financial_score = self._score_financial_impact(evidence)
        factors["financial_impact"] = financial_score

        total_score = (
            action_score * self.weights["action_type"]
            + scope_score * self.weights["scope_violation_risk"]
            + sensitivity_score * self.weights["data_sensitivity"]
            + financial_score * self.weights["financial_impact"]
        )

        risk_level = self._score_to_level(total_score)
        requires_approval = risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        auto_approve = total_score <= self.AUTO_APPROVE_THRESHOLD

        return RiskAssessment(
            score=round(total_score, 2),
            level=risk_level,
            factors=factors,
            requires_approval=requires_approval,
            auto_approve=auto_approve,
        )

    def _score_action_type(
        self, action_type: str, permission: PermissionLevel
    ) -> float:
        """Score based on action type and plugin permission level."""
        base_scores = {
            "recon": 10,
            "scan": 20,
            "test": 40,
            "exploit": 70,
            "modify": 80,
            "submit": 30,
        }

        action_score = base_scores.get(action_type.lower(), 50)

        permission_multipliers = {
            PermissionLevel.SAFE: 0.5,
            PermissionLevel.LIMITED: 1.0,
            PermissionLevel.DANGEROUS: 1.5,
        }

        return action_score * permission_multipliers.get(permission, 1.0)

    def _score_scope_risk(self, target: str, scope_info: dict | None) -> float:
        """Score based on scope risk factors."""
        if not scope_info:
            return 50

        score = 30

        if scope_info.get("is_excluded"):
            return 100

        if scope_info.get("contains_sensitive_data"):
            score += 20

        if scope_info.get("is_production"):
            score += 15

        if scope_info.get("has_critical_service"):
            score += 10

        return min(score, 100)

    def _score_financial_impact(self, evidence: dict | None) -> float:
        """Score based on potential financial impact."""
        if not evidence:
            return 30

        impact_indicators = {
            "has_pii": 20,
            "has_credentials": 30,
            "has_payment_data": 40,
            "has_health_data": 35,
            "has_oauth_tokens": 25,
        }

        score = 20
        for indicator, value in impact_indicators.items():
            if evidence.get(indicator):
                score += value

        return min(score, 100)

    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level."""
        if score >= self.SCORE_THRESHOLDS[RiskLevel.HIGH]:
            return RiskLevel.CRITICAL
        elif score >= self.SCORE_THRESHOLDS[RiskLevel.MEDIUM]:
            return RiskLevel.HIGH
        elif score >= self.SCORE_THRESHOLDS[RiskLevel.LOW]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def get_approval_requirement(
        self, risk_level: RiskLevel, program_policy: dict | None = None
    ) -> dict:
        """Determine if approval is required based on risk and program policy."""
        if program_policy and program_policy.get("auto_approve_low_risk"):
            if risk_level == RiskLevel.LOW:
                return {"required": False, "type": "none"}

        approval_rules = {
            RiskLevel.LOW: {"required": False, "type": "none"},
            RiskLevel.MEDIUM: {"required": False, "type": "notification"},
            RiskLevel.HIGH: {"required": True, "type": "approval"},
            RiskLevel.CRITICAL: {"required": True, "type": "explicit_approval"},
        }

        return approval_rules.get(risk_level, approval_rules[RiskLevel.MEDIUM])
