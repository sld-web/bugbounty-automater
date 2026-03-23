"""GitHub monitoring service for intelligence gathering."""
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubMonitor:
    """Monitor GitHub for security-relevant information."""

    SECRET_PATTERNS = [
        (r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}", "potential_api_key", "medium"),
        (r"ghp_[a-zA-Z0-9]{36}", "github_personal_token", "critical"),
        (r"gho_[a-zA-Z0-9]{36}", "github_oauth_token", "critical"),
        (r"ghu_[a-zA-Z0-9]{36}", "github_user_to_server", "critical"),
        (r"ghs_[a-zA-Z0-9]{36}", "github_server_oauth", "critical"),
        (r"ghr_[a-zA-Z0-9]{36}", "github_refresh_token", "critical"),
        (r"xoxb-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{20,}", "slack_token", "critical"),
        (r"xoxp-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{20,}", "slack_user_token", "critical"),
        (r"AKIA[A-Z0-9]{16}", "aws_access_key", "critical"),
        (r"[a-zA-Z0-9/+=]{40}", "generic_secret", "medium"),
        (r"password['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9@$!%*#?&]{8,}", "hardcoded_password", "high"),
        (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "private_key", "critical"),
        (r"sk-[a-zA-Z0-9]{48}", "openai_api_key", "critical"),
        (r"sk-proj-[a-zA-Z0-9_-]{48,}", "openai_project_key", "critical"),
    ]

    VULNERABLE_PATTERN = re.compile(
        r"(?i)(vulnerable|exploit|CVE-\d{4}-\d{4,7}|security\s+bug|critical\s+fix)"
    )

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            self._client = httpx.AsyncClient(
                base_url=GITHUB_API,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Search GitHub code with advanced query."""
        results = []
        page = 1

        while len(results) < limit:
            params = {
                "q": query,
                "per_page": min(100, limit - len(results)),
                "page": page,
                "sort": "indexed",
                "order": "desc",
            }
            if language:
                params["q"] += f" language:{language}"

            try:
                response = await self.client.get("/search/code", params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("items"):
                    break

                results.extend(data["items"])
                page += 1

                if not data.get("incomplete_results"):
                    break

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.warning("GitHub API rate limit hit")
                    break
                elif e.response.status_code == 401:
                    raise PermissionError("GitHub API authentication required")
                raise

        return results[:limit]

    async def search_repositories(
        self,
        query: str,
        limit: int = 50,
    ) -> list[dict]:
        """Search GitHub repositories."""
        results = []
        page = 1

        while len(results) < limit:
            params = {
                "q": query,
                "per_page": min(100, limit - len(results)),
                "page": page,
                "sort": "stars",
                "order": "desc",
            }

            try:
                response = await self.client.get("/search/repositories", params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("items"):
                    break

                results.extend(data["items"])
                page += 1

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.warning("GitHub API rate limit hit")
                    break
                raise

        return results[:limit]

    async def get_file_content(self, repo: str, path: str, ref: str = "main") -> Optional[str]:
        """Get file content from a repository."""
        try:
            response = await self.client.get(f"/repos/{repo}/contents/{path}", params={"ref": ref})
            response.raise_for_status()
            data = response.json()

            if data.get("encoding") == "base64":
                import base64
                return base64.b64decode(data["content"]).decode("utf-8")

            return data.get("content")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def scan_file_for_secrets(self, content: str, filename: str) -> list[dict]:
        """Scan file content for potential secrets."""
        findings = []

        for pattern, secret_type, severity in self.SECRET_PATTERNS:
            regex = re.compile(pattern)
            matches = regex.finditer(content)

            for match in matches:
                findings.append({
                    "type": "secret",
                    "subtype": secret_type,
                    "severity": severity,
                    "matched": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0),
                    "file": filename,
                    "line_hint": f"Pattern matched at position {match.start()}",
                })

        if self.VULNERABLE_PATTERN.search(content):
            findings.append({
                "type": "vulnerability_mention",
                "severity": "medium",
                "file": filename,
                "note": "File contains references to vulnerabilities or security issues",
            })

        return findings

    async def monitor_organization(
        self,
        org: str,
        credential_ids: Optional[list[str]] = None,
    ) -> list[dict]:
        """Monitor an organization's repositories."""
        all_findings = []

        try:
            repos_response = await self.client.get(f"/orgs/{org}/repos", params={"per_page": 100})
            repos_response.raise_for_status()
            repos = repos_response.json()

            logger.info(f"Monitoring {len(repos)} repositories in {org}")

            for repo in repos:
                repo_name = repo["full_name"]
                findings = await self._scan_repository(repo_name)
                all_findings.extend(findings)

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to monitor org {org}: {e}")
            if e.response.status_code == 404:
                logger.error(f"Organization {org} not found")
            elif e.response.status_code == 403:
                logger.error(f"Access denied to organization {org}")

        return all_findings

    async def _scan_repository(self, repo: str) -> list[dict]:
        """Scan a single repository for secrets."""
        findings = []

        sensitive_paths = [
            ".env",
            "config/secrets.yml",
            "secrets.yaml",
            "credentials.json",
            "settings.py",
            "config.py",
            ".aws/credentials",
            "id_rsa",
            "*.pem",
            "*.key",
            "*.p12",
        ]

        for path in sensitive_paths:
            content = await self.get_file_content(repo, path)
            if content:
                file_findings = await self.scan_file_for_secrets(content, f"{repo}/{path}")
                for f in file_findings:
                    f["repository"] = repo
                findings.extend(file_findings)

        return findings

    async def check_breach(self, email: str) -> dict:
        """Check if an email has been in known breaches (using HaveIBeenPwned API style)."""
        return {
            "email": email,
            "breached": False,
            "source": "github_monitor",
            "note": "Breach checking requires HaveIBeenPwned API integration",
        }

    async def get_repo_security_advisories(self, repo: str) -> list[dict]:
        """Get security advisories for a repository."""
        try:
            response = await self.client.get(f"/repos/{repo}/security-advisories")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            return []

    async def monitor_repo_commits(
        self,
        repo: str,
        since_days: int = 7,
    ) -> list[dict]:
        """Monitor recent commits for suspicious patterns."""
        since = datetime.utcnow() - timedelta(days=since_days)

        try:
            response = await self.client.get(
                f"/repos/{repo}/commits",
                params={"since": since.isoformat(), "per_page": 100}
            )
            response.raise_for_status()
            commits = response.json()

            suspicious = []
            for commit in commits:
                message = commit.get("commit", {}).get("message", "").lower()

                if any(x in message for x in ["secret", "api key", "password", "credentials"]):
                    suspicious.append({
                        "sha": commit["sha"],
                        "message": commit["commit"]["message"],
                        "author": commit["commit"]["author"]["name"],
                        "date": commit["commit"]["author"]["date"],
                        "url": commit["html_url"],
                        "risk": "high",
                        "reason": "Commit message suggests credential handling",
                    })

            return suspicious

        except httpx.HTTPStatusError:
            return []


class LeakDetector:
    """Detect leaked credentials and sensitive data."""

    LEAK_PATTERNS = {
        "aws": [
            r"AKIA[A-Z0-9]{16}",
            r"aws[_-]?(access[_-]?key|secret)[_-]?(id|key)?\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{20,40}",
        ],
        "github": [
            r"ghp_[a-zA-Z0-9]{36}",
            r"gho_[a-zA-Z0-9]{36}",
            r"ghr_[a-zA-Z0-9]{36}",
        ],
        "slack": [
            r"xox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{20,}",
        ],
        "database": [
            r"(mongodb|mysql|postgresql|redis):\/\/[^\s'\"]{10,}",
            r"mongodb\+srv:\/\/[^\s'\"]{10,}",
        ],
        "jwt": [
            r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        ],
    }

    def __init__(self):
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        for category, patterns in self.LEAK_PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def scan_content(self, content: str, source: str = "unknown") -> list[dict]:
        """Scan content for leaked secrets."""
        findings = []

        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(content)
                for match in matches:
                    matched_text = match.group(0)
                    masked = self._mask_secret(matched_text)

                    findings.append({
                        "type": "secret_leak",
                        "category": category,
                        "severity": self._get_severity(category),
                        "masked_value": masked,
                        "position": match.start(),
                        "source": source,
                        "message": f"Potential {category} credential found",
                    })

        return findings

    def _mask_secret(self, secret: str) -> str:
        """Mask a secret for safe logging."""
        if len(secret) <= 8:
            return "*" * len(secret)

        visible_start = min(4, len(secret) // 4)
        visible_end = min(4, len(secret) // 4)
        return secret[:visible_start] + "*" * (len(secret) - visible_start - visible_end) + secret[-visible_end:]

    def _get_severity(self, category: str) -> str:
        severity_map = {
            "aws": "critical",
            "github": "critical",
            "slack": "high",
            "database": "critical",
            "jwt": "high",
        }
        return severity_map.get(category, "medium")
