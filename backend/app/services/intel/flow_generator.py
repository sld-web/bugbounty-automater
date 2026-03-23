"""Auto-expansion service for generating flow cards from reconnaissance data."""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


ENDPOINT_PATTERNS = {
    "login": {
        "patterns": [
            r"/login",
            r"/signin",
            r"/sign-in",
            r"/auth",
            r"/authenticate",
            r"/verify",
            r"/session",
        ],
        "flow_type": "authentication",
        "attack_types": ["credential_stuffing", "brute_force", "csrf_bypass"],
    },
    "password_reset": {
        "patterns": [
            r"/forgot",
            r"/reset",
            r"/password",
            r"/recover",
            r"/lost-password",
        ],
        "flow_type": "password_reset",
        "attack_types": ["account_takeover", "email_hijacking", "token_prediction"],
    },
    "registration": {
        "patterns": [
            r"/register",
            r"/signup",
            r"/sign-up",
            r"/join",
            r"/create-account",
        ],
        "flow_type": "registration",
        "attack_types": ["duplicate_email", "username_enumeration"],
    },
    "api_endpoint": {
        "patterns": [
            r"/api/",
            r"/v\d+/",
            r"/graphql",
            r"/rest/",
            r"/endpoint",
        ],
        "flow_type": "api",
        "attack_types": ["api_key_leak", "idor", "mass_assignment", "graphql_introspection"],
    },
    "file_upload": {
        "patterns": [
            r"/upload",
            r"/upload/",
            r"/file",
            r"/attach",
            r"/profile/picture",
        ],
        "flow_type": "file_upload",
        "attack_types": ["rce", "path_traversal", "xss", "svg_upload"],
    },
    "profile": {
        "patterns": [
            r"/profile",
            r"/account",
            r"/settings",
            r"/user/",
            r"/me",
        ],
        "flow_type": "profile_management",
        "attack_types": ["idor", "csrf", "stored_xss", "parameter_pollution"],
    },
    "payment": {
        "patterns": [
            r"/checkout",
            r"/payment",
            r"/billing",
            r"/subscribe",
            r"/order",
            r"/cart",
        ],
        "flow_type": "payment",
        "attack_types": ["price_manipulation", "csrf", "race_condition", "stored_xss"],
    },
    "admin": {
        "patterns": [
            r"/admin",
            r"/dashboard",
            r"/manage",
            r"/cms",
            r"/wp-admin",
            r"/administrator",
        ],
        "flow_type": "admin_panel",
        "attack_types": ["auth_bypass", "idor", "sql_injection", "rce"],
    },
    "oauth": {
        "patterns": [
            r"/oauth",
            r"/oauth/authorize",
            r"/oauth/token",
            r"/callback",
            r"/connect",
        ],
        "flow_type": "oauth_flow",
        "attack_types": ["redirect_uri", "state_parameter", "token_leak"],
    },
    "websocket": {
        "patterns": [
            r"/ws",
            r"/websocket",
            r"/socket",
        ],
        "flow_type": "websocket",
        "attack_types": ["xss", "idor_via_websocket", "dos"],
    },
}


METHOD_ATTACKS = {
    "POST": ["sql_injection", "xss", "command_injection", "xxe", "csrf"],
    "PUT": ["overwrite", "csrf", "idempotency_issues"],
    "PATCH": ["csrf", "partial_update_idor"],
    "DELETE": ["csrf", "idor", "resource_exhaustion"],
    "GET": ["sqli", "xss", "open_redirect", "ssrf"],
}


class FlowCardGenerator:
    """Generate flow cards from discovered endpoints."""

    def __init__(self):
        self.compiled_patterns = {}
        for flow_type, config in ENDPOINT_PATTERNS.items():
            self.compiled_patterns[flow_type] = {
                "regexes": [re.compile(p, re.I) for p in config["patterns"]],
                "attack_types": config["attack_types"],
                "flow_type": config["flow_type"],
            }

    def detect_flow_type(self, endpoint: str) -> Optional[dict]:
        """Detect flow type from endpoint path."""
        for flow_type, config in self.compiled_patterns.items():
            for regex in config["regexes"]:
                if regex.search(endpoint):
                    return {
                        "flow_type": config["flow_type"],
                        "matched_pattern": regex.pattern,
                        "attack_types": config["attack_types"],
                    }
        return None

    def generate_flow_cards(
        self,
        endpoints: list[dict],
        target_id: str,
    ) -> list[dict]:
        """Generate flow cards from discovered endpoints."""
        flow_cards = []
        seen_flows = set()

        for endpoint in endpoints:
            path = endpoint.get("path", "")
            method = endpoint.get("method", "GET").upper()

            flow_detection = self.detect_flow_type(path)

            if flow_detection:
                flow_key = f"{flow_detection['flow_type']}:{path}"
                if flow_key in seen_flows:
                    continue
                seen_flows.add(flow_key)

                card = self._create_flow_card(
                    flow_type=flow_detection["flow_type"],
                    endpoint=endpoint,
                    target_id=target_id,
                    attack_types=flow_detection["attack_types"],
                )
                flow_cards.append(card)

            method_attacks = METHOD_ATTACKS.get(method, [])
            if method_attacks and method not in ["GET"]:
                card = self._create_method_based_card(
                    endpoint=endpoint,
                    method=method,
                    target_id=target_id,
                    attack_types=method_attacks,
                )
                flow_cards.append(card)

        return flow_cards

    def _create_flow_card(
        self,
        flow_type: str,
        endpoint: dict,
        target_id: str,
        attack_types: list[str],
    ) -> dict:
        """Create a flow card for a detected flow type."""
        return {
            "card_type": "flow",
            "flow_type": flow_type,
            "title": self._generate_title(flow_type, endpoint.get("path", "")),
            "description": self._generate_description(flow_type, endpoint),
            "endpoint": endpoint.get("path", ""),
            "method": endpoint.get("method", "GET"),
            "target_id": target_id,
            "attack_types": attack_types,
            "test_cases": self._generate_test_cases(flow_type, attack_types),
            "status": "pending",
        }

    def _create_method_based_card(
        self,
        endpoint: dict,
        method: str,
        target_id: str,
        attack_types: list[str],
    ) -> dict:
        """Create a flow card based on HTTP method."""
        return {
            "card_type": "attack",
            "flow_type": "method_based",
            "title": f"{method} {endpoint.get('path', '/')}",
            "description": f"Test {method} requests to {endpoint.get('path', '/')} for common vulnerabilities",
            "endpoint": endpoint.get("path", ""),
            "method": method,
            "target_id": target_id,
            "attack_types": attack_types,
            "test_cases": self._generate_method_test_cases(method, endpoint),
            "status": "pending",
        }

    def _generate_title(self, flow_type: str, path: str) -> str:
        """Generate a title for the flow card."""
        flow_names = {
            "authentication": "Login Flow",
            "password_reset": "Password Reset Flow",
            "registration": "Registration Flow",
            "api": "API Endpoint",
            "file_upload": "File Upload",
            "profile_management": "Profile Management",
            "payment": "Payment Flow",
            "admin_panel": "Admin Panel",
            "oauth_flow": "OAuth Flow",
            "websocket": "WebSocket Connection",
        }
        name = flow_names.get(flow_type, flow_type.replace("_", " ").title())
        return f"{name}: {path}"

    def _generate_description(self, flow_type: str, endpoint: dict) -> str:
        """Generate description for the flow card."""
        descriptions = {
            "authentication": f"Authentication endpoint found at {endpoint.get('path')}. Test for credential stuffing, brute force, and authentication bypasses.",
            "password_reset": f"Password reset flow at {endpoint.get('path')}. Test for account takeover vulnerabilities.",
            "registration": f"User registration at {endpoint.get('path')}. Test for email/username enumeration.",
            "api": f"API endpoint at {endpoint.get('path')}. Test for IDOR, mass assignment, and information disclosure.",
            "file_upload": f"File upload functionality at {endpoint.get('path')}. Test for RCE, path traversal, and XSS.",
            "profile_management": f"Profile management at {endpoint.get('path')}. Test for IDOR and stored XSS.",
            "payment": f"Payment/checkout at {endpoint.get('path')}. Test for price manipulation and race conditions.",
            "admin_panel": f"Admin interface at {endpoint.get('path')}. Test for auth bypass and privilege escalation.",
            "oauth_flow": f"OAuth flow at {endpoint.get('path')}. Test for redirect URI bypass and token leakage.",
            "websocket": f"WebSocket at {endpoint.get('path')}. Test for XSS and DoS via websocket.",
        }
        return descriptions.get(flow_type, f"Flow at {endpoint.get('path')}")

    def _generate_test_cases(self, flow_type: str, attack_types: list[str]) -> list[dict]:
        """Generate test cases for the flow."""
        test_cases = []
        for attack in attack_types:
            test_case = self._get_test_case_template(attack)
            if test_case:
                test_cases.append(test_case)
        return test_cases

    def _generate_method_test_cases(self, method: str, endpoint: dict) -> list[dict]:
        """Generate test cases based on HTTP method."""
        test_cases = []
        attacks = METHOD_ATTACKS.get(method, [])

        for attack in attacks:
            test_case = self._get_test_case_template(attack)
            if test_case:
                test_cases.append(test_case)

        return test_cases

    def _get_test_case_template(self, attack_type: str) -> Optional[dict]:
        """Get test case template for an attack type."""
        templates = {
            "sql_injection": {
                "name": "SQL Injection Test",
                "payloads": ["'", "' OR 1=1--", "'; DROP TABLE users--"],
                "expected": "Database error or unexpected behavior",
            },
            "xss": {
                "name": "Cross-Site Scripting Test",
                "payloads": ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"],
                "expected": "Script executes or reflects",
            },
            "csrf": {
                "name": "CSRF Test",
                "payloads": ["Check for CSRF token presence"],
                "expected": "Action succeeds without valid token",
            },
            "idor": {
                "name": "IDOR Test",
                "payloads": ["Change ID parameter in request"],
                "expected": "Access to unauthorized resource",
            },
            "rce": {
                "name": "Remote Code Execution Test",
                "payloads": ["; ls", "| cat /etc/passwd", "$(whoami)"],
                "expected": "Command output returned",
            },
            "auth_bypass": {
                "name": "Authentication Bypass Test",
                "payloads": ["admin'--", "admin' OR '1'='1"],
                "expected": "Gain unauthorized access",
            },
            "path_traversal": {
                "name": "Path Traversal Test",
                "payloads": ["../etc/passwd", "..%2F..%2Fetc/passwd"],
                "expected": "File contents returned",
            },
            "command_injection": {
                "name": "Command Injection Test",
                "payloads": ["; cat /etc/passwd", "| ls", "`whoami`"],
                "expected": "Command executed",
            },
            "stored_xss": {
                "name": "Stored XSS Test",
                "payloads": ["<script>alert(1)</script>"],
                "expected": "Script stored and executes on page load",
            },
            "open_redirect": {
                "name": "Open Redirect Test",
                "payloads": ["https://evil.com", "//evil.com"],
                "expected": "Redirect to external site",
            },
            "ssrf": {
                "name": "SSRF Test",
                "payloads": ["http://localhost", "http://169.254.169.254"],
                "expected": "Internal resource accessed",
            },
            "xxe": {
                "name": "XXE Test",
                "payloads": ["<?xml version=\"1.0\"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><foo>&xxe;</foo>"],
                "expected": "External entity resolved",
            },
        }
        return templates.get(attack_type)
