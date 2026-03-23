"""Bugcrowd API integration for report submission."""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class BugcrowdAPI:
    """Bugcrowd API client for report submission."""

    BASE_URL = "https://bugcrowd.com/api/v2"

    def __init__(self, api_key: str, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Authorization": f"Token token={self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def get_programs(self) -> dict:
        """Get list of accessible programs."""
        try:
            response = await self.client.get(f"{self.BASE_URL}/programs.json")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get programs: {e}")
            return {"programs": []}

    async def create_submission(
        self,
        program_handle: str,
        title: str,
        description: str,
        severity: str,
        impact: str,
        steps_to_reproduce: str,
        remediation: Optional[str] = None,
        cvss_score: Optional[float] = None,
    ) -> dict:
        """Create a new vulnerability submission."""
        if not self.api_key or self.api_key == "test":
            return {
                "success": False,
                "error": "Invalid or missing API key",
                "mock": True,
            }
        
        try:
            payload = {
                "title": title,
                "description": description,
                "severity": severity,
                "impact": impact,
                "steps_to_reproduce": steps_to_reproduce,
            }

            if remediation:
                payload["remediation_advice"] = remediation

            if cvss_score:
                payload["cvss_score"] = str(cvss_score)

            response = await self.client.post(
                f"{self.BASE_URL}/program/{program_handle}/submissions.json",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "submission_id": data.get("id"),
                "status": data.get("status"),
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to create submission: {e}")
            return {"success": False, "error": str(e)}

    async def get_submission(self, submission_id: str) -> dict:
        """Get submission details."""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/submissions/{submission_id}.json"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get submission: {e}")
            return {"error": str(e)}

    async def add_evidence(
        self,
        submission_id: str,
        evidence_type: str,
        content: str,
    ) -> dict:
        """Add evidence to a submission."""
        try:
            payload = {
                "evidence": {
                    "type": evidence_type,
                    "body": content,
                }
            }

            response = await self.client.post(
                f"{self.BASE_URL}/submissions/{submission_id}/evidence.json",
                json=payload,
            )
            response.raise_for_status()
            return {"success": True}

        except httpx.HTTPError as e:
            logger.error(f"Failed to add evidence: {e}")
            return {"success": False, "error": str(e)}

    async def add_file(
        self,
        submission_id: str,
        file_data: bytes,
        filename: str,
    ) -> dict:
        """Add file evidence to a submission."""
        try:
            files = {"file": (filename, file_data)}
            response = await self.client.post(
                f"{self.BASE_URL}/submissions/{submission_id}/files.json",
                files=files,
            )
            response.raise_for_status()
            return {"success": True}

        except httpx.HTTPError as e:
            logger.error(f"Failed to add file: {e}")
            return {"success": False, "error": str(e)}
