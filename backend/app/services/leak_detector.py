"""Leak detection service for monitoring exposed credentials and data."""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class LeakDetector:
    """Service for detecting leaked credentials and sensitive data."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def check_email(self, email: str) -> dict:
        """Check if an email has been involved in known data breaches."""
        try:
            response = await self.client.get(
                f"https://haveibeenpwned.com/api/v3/breach/{email}"
            )
            if response.status_code == 404:
                return {"breached": False, "breaches": []}
            response.raise_for_status()
            return {"breached": True, "breaches": response.json()}
        except httpx.HTTPError as e:
            logger.error(f"Failed to check email: {e}")
            return {"breached": False, "error": str(e)}

    async def check_password(self, password: str) -> dict:
        """Check if a password has been exposed in data breaches."""
        import hashlib

        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        try:
            response = await self.client.get(
                f"https://api.pwnedpasswords.com/range/{prefix}"
            )
            response.raise_for_status()

            for line in response.text.split("\n"):
                hash_suffix, count = line.strip().split(":")
                if hash_suffix == suffix:
                    return {
                        "compromised": True,
                        "occurrences": int(count),
                    }

            return {"compromised": False, "occurrences": 0}

        except httpx.HTTPError as e:
            logger.error(f"Failed to check password: {e}")
            return {"compromised": False, "error": str(e)}

    async def search_github_leaks(
        self,
        domain: str,
        patterns: Optional[list[str]] = None,
    ) -> dict:
        """Search GitHub for potential leaked secrets."""
        if patterns is None:
            patterns = [
                f"{domain}",
                "password",
                "secret",
                "api_key",
                "token",
            ]

        results = []
        for pattern in patterns:
            try:
                response = await self.client.get(
                    "https://api.github.com/search/code",
                    params={
                        "q": f"{pattern} {domain}",
                        "per_page": 10,
                    },
                )
                response.raise_for_status()
                data = response.json()
                results.extend(data.get("items", []))
            except httpx.HTTPError as e:
                logger.warning(f"GitHub search failed for pattern '{pattern}': {e}")

        return {
            "domain": domain,
            "total_results": len(results),
            "results": [
                {
                    "name": r.get("name"),
                    "repository": r.get("repository", {}).get("full_name"),
                    "path": r.get("path"),
                    "url": r.get("html_url"),
                }
                for r in results[:50]
            ],
        }

    async def search_exposed_api_keys(
        self,
        key_pattern: str,
    ) -> dict:
        """Search for exposed API keys matching a pattern."""
        try:
            response = await self.client.get(
                "https://api.github.com/search/code",
                params={
                    "q": f'"{key_pattern}"',
                    "per_page": 20,
                },
            )
            response.raise_for_status()
            data = response.json()

            return {
                "pattern": key_pattern,
                "total_count": data.get("total_count", 0),
                "matches": [
                    {
                        "repository": item.get("repository", {}).get("full_name"),
                        "path": item.get("path"),
                        "url": item.get("html_url"),
                    }
                    for item in data.get("items", [])[:20]
                ],
            }
        except httpx.HTTPError as e:
            logger.error(f"Failed to search for API keys: {e}")
            return {"pattern": key_pattern, "error": str(e)}


def get_leak_detector(api_key: Optional[str] = None) -> LeakDetector:
    """Get leak detector instance."""
    return LeakDetector(api_key)
