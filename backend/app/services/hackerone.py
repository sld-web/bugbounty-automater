"""HackerOne API integration."""
import logging
from typing import Any

import aiohttp

from app.external_config import get_external_apis

logger = logging.getLogger(__name__)


class HackerOneService:
    """Integrate with HackerOne API."""

    def __init__(self):
        external_apis = get_external_apis()
        self.api_token = external_apis.hackerone_api_token
        self.api_url = external_apis.hackerone_api_url
        self.username = external_apis.hackerone_username

    async def get_program(self, program_handle: str) -> dict | None:
        """Get program details."""
        headers = self._get_headers()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/programs/{program_handle}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.error(f"HackerOne API error: {resp.status}")

        except Exception as e:
            logger.error(f"Failed to fetch program: {e}")

        return None

    async def get_scope(self, program_handle: str) -> dict | None:
        """Get program scope."""
        headers = self._get_headers()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/programs/{program_handle}/structured_scopes",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.error(f"HackerOne API error: {resp.status}")

        except Exception as e:
            logger.error(f"Failed to fetch scope: {e}")

        return None

    async def submit_report(
        self,
        program_handle: str,
        title: str,
        description: str,
        severity: str,
        vulnerable_url: str,
        weakness: str | None = None,
        impact: str | None = None,
        remediation: str | None = None,
    ) -> dict | None:
        """Submit a vulnerability report."""
        headers = self._get_headers()

        report_data = {
            "data": {
                "type": "report",
                "attributes": {
                    "title": title,
                    "description": description,
                    "severity_rating": severity.lower(),
                    "vulnerable_url": vulnerable_url,
                    "weakness": {"name": weakness} if weakness else None,
                    "impact": impact,
                    "remediation_guidance": remediation,
                },
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/reports",
                    json=report_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    logger.error(f"Report submission error: {resp.status}")
                    error_text = await resp.text()
                    logger.error(f"Error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to submit report: {e}")

        return None

    async def list_reports(
        self,
        program_handle: str,
        state: str | None = None,
    ) -> list[dict]:
        """List reports for a program."""
        headers = self._get_headers()

        params = {}
        if state:
            params["filter[state]"] = state

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/reports",
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", [])
                    logger.error(f"HackerOne API error: {resp.status}")

        except Exception as e:
            logger.error(f"Failed to list reports: {e}")

        return []

    def _get_headers(self) -> dict:
        """Get authentication headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers
