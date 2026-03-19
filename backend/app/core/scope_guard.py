"""Scope guard for validating targets against program scope."""
import fnmatch
import re
from urllib.parse import urlparse

import tldextract


class ScopeGuard:
    """Validate targets against program scope."""

    def __init__(self, scope_domains: list[str], excluded: list[str] | None = None):
        self.scope_domains = scope_domains
        self.excluded = excluded or []

    def is_in_scope(self, target: str) -> tuple[bool, dict]:
        """Check if target is within scope.
        
        Returns:
            Tuple of (is_in_scope, scope_info)
        """
        scope_info = {
            "is_in_scope": False,
            "is_excluded": False,
            "matched_pattern": None,
            "contains_sensitive_data": False,
            "is_production": False,
            "has_critical_service": False,
        }

        target_clean = self._normalize_target(target)
        if not target_clean:
            return False, scope_info

        for pattern in self.excluded:
            if self._matches_pattern(target_clean, pattern):
                return False, {**scope_info, "is_excluded": True}

        for pattern in self.scope_domains:
            if self._matches_pattern(target_clean, pattern):
                scope_info["is_in_scope"] = True
                scope_info["matched_pattern"] = pattern
                scope_info["is_production"] = "staging" not in target_clean.lower()
                scope_info["has_critical_service"] = self._is_critical_service(
                    target_clean
                )
                return True, scope_info

        return False, scope_info

    def filter_scope(self, targets: list[str]) -> tuple[list[str], list[str]]:
        """Filter list of targets by scope.
        
        Returns:
            Tuple of (in_scope_targets, out_of_scope_targets)
        """
        in_scope = []
        out_of_scope = []

        for target in targets:
            is_in, _ = self.is_in_scope(target)
            if is_in:
                in_scope.append(target)
            else:
                out_of_scope.append(target)

        return in_scope, out_of_scope

    def _normalize_target(self, target: str) -> str | None:
        """Normalize target string."""
        if not target:
            return None

        target = target.strip().lower()

        if target.startswith(("http://", "https://")):
            parsed = urlparse(target)
            return parsed.netloc or parsed.path

        if target.startswith("*."):
            target = target[2:]

        return target

    def _matches_pattern(self, target: str, pattern: str) -> bool:
        """Check if target matches a scope pattern."""
        pattern = pattern.strip().lower()

        if pattern.startswith("*."):
            base_domain = pattern[2:]
            return target.endswith(base_domain) or target == base_domain

        if "*" in pattern:
            return fnmatch.fnmatch(target, pattern)

        return target == pattern or target.endswith(f".{pattern}")

    def _is_critical_service(self, target: str) -> bool:
        """Determine if target is a critical service."""
        critical_patterns = [
            r"^(api|admin|cpanel|mail|ftp|ssh|dns|db|database)",
            r"(auth|login|oauth|saml|sso)",
            r"(payment|billing|invoice|subscription)",
            r"(bank|finance|wallet)",
            r"(admin|dashboard|cms)",
        ]

        for pattern in critical_patterns:
            if re.match(pattern, target):
                return True

        return False

    def extract_domain(self, target: str) -> str | None:
        """Extract root domain from target."""
        normalized = self._normalize_target(target)
        if not normalized:
            return None

        extracted = tldextract.extract(normalized)
        return f"{extracted.domain}.{extracted.suffix}"

    def expand_wildcards(self, pattern: str) -> list[str]:
        """Expand wildcard patterns to potential subdomains."""
        if "*." not in pattern:
            return [pattern]

        base_domain = pattern.replace("*.", "")

        common_subdomains = [
            "www",
            "api",
            "mail",
            "ftp",
            "localhost",
            "webmail",
            "smtp",
            "pop",
            "ns1",
            "webdisk",
            "ns2",
            "cpanel",
            "whm",
            "autodiscover",
            "autoconfig",
            "m",
            "imap",
            "test",
            "ns",
            "blog",
            "pop3",
            "dev",
            "www2",
            "admin",
            "forum",
            "news",
            "vpn",
            "ns3",
            "mail2",
            "new",
            "mysql",
            "old",
            "lists",
            "support",
            "mobile",
            "mx",
            "static",
            "docs",
            "beta",
            "shop",
            "sql",
            "secure",
            "demo",
            "cp",
            "calendar",
            "wiki",
            "web",
        ]

        return [f"{sub}.{base_domain}" for sub in common_subdomains]

    @classmethod
    def from_program_config(cls, program_config: dict) -> "ScopeGuard":
        """Create ScopeGuard from program configuration."""
        return cls(
            scope_domains=program_config.get("scope_domains", []),
            excluded=program_config.get("scope_excluded", []),
        )
