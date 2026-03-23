import logging
import httpx
from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import get_db_context
from app.models.target import Target

logger = logging.getLogger(__name__)

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


async def fetch_cve_feed():
    try:
        api_key = "7598fd9d-592c-499b-b95b-ca9ca4d4233a"
        
        headers = {"apiKey": api_key}
        params = {
            "resultsPerPage": 100,
            "pubStartDate": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000")
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(NVD_API_URL, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                cves = data.get("vulnerabilities", [])
                logger.info(f"Fetched {len(cves)} CVEs from NVD")
                return cves
            else:
                logger.warning(f"NVD API returned {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Failed to fetch CVE feed: {e}")
        return []


async def sync_cve_intelligence():
    cves = await fetch_cve_feed()
    
    async with get_db_context() as db:
        result = await db.execute(select(Target))
        targets = result.scalars().all()
        
        for target in targets:
            matched = 0
            for cve in cves:
                cve_data = cve.get("cve", {})
                descriptions = cve_data.get("descriptions", [])
                for desc in descriptions:
                    if desc.get("lang") == "en":
                        text = desc.get("value", "").lower()
                        if any(domain in text for domain in target.subdomains or []):
                            matched += 1
            
            if matched > 0:
                logger.info(f"Target {target.name}: {matched} CVEs matched")
    
    return len(cves)
