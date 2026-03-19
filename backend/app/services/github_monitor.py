"""GitHub monitoring service."""
import asyncio
import logging
import re

import aiohttp

from app.external_config import get_external_apis

logger = logging.getLogger(__name__)


class GitHubMonitor:
    """Monitor GitHub for leaked credentials and sensitive data."""

    def __init__(self):
        external_apis = get_external_apis()
        self.token = external_apis.github_token
        self.base_url = "https://api.github.com"

    async def search_code(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict]:
        """Search GitHub code for sensitive patterns."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        params = {
            "q": query,
            "per_page": min(max_results, 100),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search/code",
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("items", [])
                    elif resp.status == 403:
                        logger.warning("GitHub API rate limited")
                    else:
                        logger.error(f"GitHub API error: {resp.status}")

        except Exception as e:
            logger.error(f"GitHub search failed: {e}")

        return []

    async def search_leaked_credentials(
        self,
        domains: list[str],
    ) -> list[dict]:
        """Search for potentially leaked credentials related to domains."""
        leaked = []

        patterns = [
            "password=",
            "api_key=",
            "secret=",
            "token=",
            ".env",
            "credentials.json",
        ]

        for domain in domains:
            for pattern in patterns:
                query = f"{pattern} {domain}"
                results = await self.search_code(query, max_results=5)

                for result in results:
                    leaked.append({
                        "file": result.get("path"),
                        "repository": result.get("repository", {}).get("full_name"),
                        "url": result.get("html_url"),
                        "matched_pattern": pattern,
                        "domain": domain,
                    })

        return leaked

    async def check_repo_security(
        self,
        repo: str,
    ) -> dict:
        """Check a repository for security issues."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        security_info = {
            "repo": repo,
            "vulnerabilities": [],
            "advisories": [],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/repos/{repo}/vulnerability-alerts",
                    headers=headers,
                    raise_for_status=False,
                ) as resp:
                    security_info["has_alerts"] = resp.status == 204

                async with session.get(
                    f"{self.base_url}/repos/{repo}/code-scanning/alerts",
                    headers=headers,
                    raise_for_status=False,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        security_info["vulnerabilities"] = data

                async with session.get(
                    f"{self.base_url}/repos/{repo}/dependabot/alerts",
                    headers=headers,
                    raise_for_status=False,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        security_info["advisories"] = data

        except Exception as e:
            logger.error(f"Failed to check repo {repo}: {e}")

        return security_info

    def detect_sensitive_data(self, content: str) -> dict:
        """Detect sensitive data patterns in content."""
        findings = {}

        patterns = {
            "aws_key": r"AKIA[0-9A-Z]{16}",
            "aws_secret": r"[A-Za-z0-9/+=]{40}",
            "github_token": r"ghp_[A-Za-z0-9]{36}",
            "github_oauth": r"gho_[A-Za-z0-9]{36}",
            "slack_token": r"xox[baprs]-[0-9a-zA-Z-]+",
            "private_key": r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
            "jwt": r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*",
            "generic_api_key": r"[aA][pP][iI]_?[kK][eE][yY].*['\"][A-Za-z0-9]{16,}['\"]",
            "generic_secret": r"[sS][eE][cC][rR][eE][tT].*['\"][A-Za-z0-9]{16,}['\"]",
        }

        for name, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                findings[name] = len(matches)

        return findings
