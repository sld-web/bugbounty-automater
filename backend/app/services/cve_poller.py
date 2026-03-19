"""CVE poller for NVD API integration."""
import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp

from app.external_config import get_external_apis

logger = logging.getLogger(__name__)


class CVEService:
    """Poll NVD CVE feed for new vulnerabilities."""

    def __init__(self):
        external_apis = get_external_apis()
        self.api_key = external_apis.nvd_api_key
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.last_poll = None

    async def get_recent_cves(
        self,
        days: int = 1,
        keyword: str | None = None,
    ) -> list[dict]:
        """Get CVEs published in the last N days."""
        pub_start = datetime.utcnow() - timedelta(days=days)
        pub_start_str = pub_start.strftime("%Y-%m-%dT%H:%M:%S.000")

        params = {
            "pubStartDate": pub_start_str,
            "resultsPerPage": 50,
        }

        if keyword:
            params["keywordSearch"] = keyword

        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key

        cves = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        cves = data.get("vulnerabilities", [])
                    elif resp.status == 403:
                        logger.warning("NVD API rate limited")
                    else:
                        logger.error(f"NVD API error: {resp.status}")

        except Exception as e:
            logger.error(f"Failed to fetch CVEs: {e}")

        return cves

    async def get_cve_details(self, cve_id: str) -> dict | None:
        """Get detailed information for a specific CVE."""
        params = {"cveId": cve_id}

        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        vulnerabilities = data.get("vulnerabilities", [])
                        if vulnerabilities:
                            return vulnerabilities[0]
                    else:
                        logger.error(f"NVD API error: {resp.status}")

        except Exception as e:
            logger.error(f"Failed to fetch CVE {cve_id}: {e}")

        return None

    async def match_tech_to_cves(
        self,
        technologies: list[str],
        days: int = 30,
    ) -> list[dict]:
        """Match technologies to recent CVEs."""
        matched = []

        for tech in technologies:
            cves = await self.get_recent_cves(days=days, keyword=tech)
            for cve in cves:
                cve_data = cve.get("cve", {})
                matched.append({
                    "cve_id": cve_data.get("id"),
                    "description": self._get_description(cve_data),
                    "cvss_score": self._get_cvss_score(cve_data),
                    "matched_tech": tech,
                    "references": self._get_references(cve_data),
                })

        return matched

    def _get_description(self, cve_data: dict) -> str:
        """Extract English description from CVE."""
        descriptions = cve_data.get("descriptions", [])
        for desc in descriptions:
            if desc.get("lang") == "en":
                return desc.get("value", "")
        return ""

    def _get_cvss_score(self, cve_data: dict) -> float | None:
        """Extract CVSS score from CVE."""
        metrics = cve_data.get("metrics", {})
        if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
            return metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseScore")
        if "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
            return metrics["cvssMetricV30"][0].get("cvssData", {}).get("baseScore")
        if "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
            return metrics["cvssMetricV2"][0].get("cvssData", {}).get("baseScore")
        return None

    def _get_references(self, cve_data: dict) -> list[str]:
        """Extract reference URLs from CVE."""
        references = cve_data.get("references", [])
        return [ref.get("url", "") for ref in references[:5] if ref.get("url")]
