"""Coverage tracker for measuring testing progress."""
from dataclasses import dataclass

from app.schemas.flow import CoverageResponse


@dataclass
class CoverageMetrics:
    surface_coverage: int
    attack_vector_coverage: int
    logic_flow_coverage: int
    total_assets: int
    tested_assets: int
    total_attack_vectors: int
    attempted_attack_vectors: int
    total_flows: int
    tested_flows: int


class CoverageTracker:
    """Track testing coverage across different dimensions."""

    def __init__(self):
        pass

    def calculate_surface_coverage(
        self,
        total_assets: int,
        tested_assets: int,
    ) -> int:
        """Calculate surface coverage percentage."""
        if total_assets == 0:
            return 0
        return int((tested_assets / total_assets) * 100)

    def calculate_attack_vector_coverage(
        self,
        total_vectors: int,
        attempted_vectors: int,
    ) -> int:
        """Calculate attack vector coverage percentage."""
        if total_vectors == 0:
            return 0
        return int((attempted_vectors / total_vectors) * 100)

    def calculate_flow_coverage(
        self,
        total_flows: int,
        tested_flows: int,
    ) -> int:
        """Calculate logic flow coverage percentage."""
        if total_flows == 0:
            return 0
        return int((tested_flows / total_flows) * 100)

    def get_coverage(
        self,
        target_data: dict,
        flow_cards: list[dict],
    ) -> CoverageResponse:
        """Calculate comprehensive coverage metrics for a target."""
        subdomains = target_data.get("subdomains", [])
        endpoints = target_data.get("endpoints", [])
        total_assets = len(subdomains) + len(endpoints)

        tested_endpoints = [
            e for e in endpoints if e.get("tested", False)
        ]
        tested_assets = len(tested_endpoints)

        attack_cards = [
            c for c in flow_cards if c.get("card_type") == "ATTACK"
        ]
        total_attack_vectors = len(attack_cards)
        attempted_vectors = len(
            [
                c
                for c in attack_cards
                if c.get("status") in ("RUNNING", "DONE", "FAILED")
            ]
        )

        flow_cards_only = [
            c for c in flow_cards if c.get("card_type") == "FLOW"
        ]
        total_flows = len(flow_cards_only)
        tested_flows = len(
            [c for c in flow_cards_only if c.get("status") == "DONE"]
        )

        return CoverageResponse(
            target_id=target_data.get("id", ""),
            surface_coverage=self.calculate_surface_coverage(
                total_assets, tested_assets
            ),
            attack_vector_coverage=self.calculate_attack_vector_coverage(
                total_attack_vectors, attempted_vectors
            ),
            logic_flow_coverage=self.calculate_flow_coverage(
                total_flows, tested_flows
            ),
            total_assets=total_assets,
            tested_assets=tested_assets,
            total_attack_vectors=total_attack_vectors,
            attempted_attack_vectors=attempted_vectors,
            total_flows=total_flows,
            tested_flows=tested_flows,
        )

    def get_missing_coverage(
        self,
        target_data: dict,
        flow_cards: list[dict],
        vuln_types: list[str],
    ) -> dict:
        """Identify areas with missing coverage."""
        missing = {
            "untested_assets": [],
            "untested_attack_vectors": [],
            "untested_flows": [],
            "recommended_vectors": [],
        }

        endpoints = target_data.get("endpoints", [])
        missing["untested_assets"] = [
            e.get("url") for e in endpoints if not e.get("tested", False)
        ]

        attack_cards = {
            c.get("name"): c
            for c in flow_cards
            if c.get("card_type") == "ATTACK"
        }

        for vector in vuln_types:
            if vector not in attack_cards:
                missing["untested_attack_vectors"].append(vector)

        flow_cards_only = {
            c.get("name"): c
            for c in flow_cards
            if c.get("card_type") == "FLOW"
        }

        common_flows = [
            "login",
            "password_reset",
            "registration",
            "profile_update",
            "logout",
            "api_auth",
        ]

        missing["untested_flows"] = [
            f for f in common_flows if f not in flow_cards_only
        ]

        missing["recommended_vectors"] = self._get_recommended_vectors(
            target_data, flow_cards
        )

        return missing

    def _get_recommended_vectors(
        self,
        target_data: dict,
        flow_cards: list[dict],
    ) -> list[dict]:
        """Get recommended attack vectors based on target tech stack."""
        recommendations = []
        technologies = target_data.get("technologies", [])
        existing_attacks = {
            c.get("name") for c in flow_cards if c.get("card_type") == "ATTACK"
        }

        tech_to_vectors = {
            "nginx": [{"name": "nginxMisconfig", "severity": "HIGH"}],
            "apache": [{"name": "apacheMisconfig", "severity": "HIGH"}],
            "wordpress": [
                {"name": "wp插件漏洞", "severity": "HIGH"},
                {"name": "wp主题漏洞", "severity": "MEDIUM"},
            ],
            "django": [{"name": "djangoMisconfig", "severity": "MEDIUM"}],
            "rails": [{"name": "railsMisconfig", "severity": "MEDIUM"}],
            "node": [{"name": "nodeMisconfig", "severity": "MEDIUM"}],
            "react": [{"name": "xss", "severity": "MEDIUM"}],
            "vue": [{"name": "xss", "severity": "MEDIUM"}],
            "php": [
                {"name": "sql_injection", "severity": "CRITICAL"},
                {"name": "rce", "severity": "CRITICAL"},
            ],
        }

        for tech in technologies:
            tech_lower = tech.lower()
            if tech_lower in tech_to_vectors:
                for vector in tech_to_vectors[tech_lower]:
                    if vector["name"] not in existing_attacks:
                        recommendations.append(
                            {
                                "vector": vector["name"],
                                "tech": tech,
                                "severity": vector["severity"],
                                "reason": f"Detected {tech} in stack",
                            }
                        )

        return recommendations
