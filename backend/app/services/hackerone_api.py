"""HackerOne API integration for report submission."""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class HackerOneAPI:
    """HackerOne API client for report submission."""

    BASE_URL = "https://api.hackerone.com/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def get_programs(self) -> dict:
        """Get list of accessible programs."""
        try:
            response = await self.client.get(f"{self.BASE_URL}/programs")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get programs: {e}")
            return {"programs": []}

    async def create_report(
        self,
        program_id: str,
        title: str,
        description: str,
        severity: str,
        weakness: str,
        impact: str,
        remediation: str,
        cvss_vector: Optional[str] = None,
    ) -> dict:
        """Create a new vulnerability report."""
        if not self.api_key or self.api_key == "test":
            return {
                "success": False,
                "error": "Invalid or missing API key",
                "mock": True,
            }
        
        try:
            payload = {
                "data": {
                    "type": "report",
                    "attributes": {
                        "title": title,
                        "description": description,
                        "severity_rating": severity,
                        "weakness": weakness,
                        "impact": impact,
                        "remediation_advice": remediation,
                    }
                }
            }

            if cvss_vector:
                payload["data"]["attributes"]["cvss_vector_string"] = cvss_vector

            response = await self.client.post(
                f"{self.BASE_URL}/reports",
                json=payload,
            )
            response.raise_for_status()
            return {"success": True, "report_id": response.json().get("id")}

        except httpx.HTTPError as e:
            logger.error(f"Failed to create report: {e}")
            return {"success": False, "error": str(e)}

    async def get_report(self, report_id: str) -> dict:
        """Get report details."""
        try:
            response = await self.client.get(f"{self.BASE_URL}/reports/{report_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get report: {e}")
            return {"error": str(e)}

    async def add_evidence(
        self,
        report_id: str,
        evidence_type: str,
        content: str,
    ) -> dict:
        """Add evidence to a report."""
        try:
            payload = {
                "data": {
                    "type": "activity",
                    "attributes": {
                        "activity_type": "evidence",
                        "evidence_type": evidence_type,
                        "body": content,
                    }
                }
            }

            response = await self.client.post(
                f"{self.BASE_URL}/reports/{report_id}/activities",
                json=payload,
            )
            response.raise_for_status()
            return {"success": True}

        except httpx.HTTPError as e:
            logger.error(f"Failed to add evidence: {e}")
            return {"success": False, "error": str(e)}

    async def add_screenshot(
        self,
        report_id: str,
        image_data: str,
        filename: str,
    ) -> dict:
        """Add screenshot evidence to a report."""
        try:
            import base64

            files = {
                "file": (filename, base64.b64decode(image_data), "image/png"),
            }
            data = {"type": "screenshot"}

            response = await self.client.post(
                f"{self.BASE_URL}/reports/{report_id}/attachments",
                files=files,
                data=data,
            )
            response.raise_for_status()
            return {"success": True, "attachment_id": response.json().get("id")}

        except httpx.HTTPError as e:
            logger.error(f"Failed to add screenshot: {e}")
            return {"success": False, "error": str(e)}

    async def close_report(
        self,
        report_id: str,
        resolution: str = "resolved",
        message: Optional[str] = None,
    ) -> dict:
        """Close a report."""
        try:
            payload = {
                "data": {
                    "attributes": {
                        "resolution": resolution,
                    }
                }
            }

            if message:
                payload["data"]["attributes"]["message"] = message

            response = await self.client.patch(
                f"{self.BASE_URL}/reports/{report_id}",
                json=payload,
            )
            response.raise_for_status()
            return {"success": True}

        except httpx.HTTPError as e:
            logger.error(f"Failed to close report: {e}")
            return {"success": False, "error": str(e)}
