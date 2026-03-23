"""API verification endpoints."""
from fastapi import APIRouter

from app.services.api_verifier import api_verifier

router = APIRouter(prefix="/verify", tags=["verification"])


@router.get("/apis")
async def verify_all_apis():
    """Verify connectivity and status of all external APIs.
    
    Returns status for:
    - AI: OpenAI
    - Intelligence: Shodan, Censys, NVD, GitHub, VirusTotal, AlienVault OTX, SecurityTrails, Hunter.io, LeakLookup
    - Notifications: Slack
    """
    results = await api_verifier.verify_all()
    
    summary = {
        "total": len(results),
        "healthy": sum(1 for r in results if r.status == "healthy"),
        "configured": sum(1 for r in results if r.configured),
        "not_configured": sum(1 for r in results if not r.configured),
        "errors": sum(1 for r in results if r.status == "error"),
    }
    
    return {
        "summary": summary,
        "apis": [
            {
                "name": r.name,
                "category": r.category,
                "configured": r.configured,
                "status": r.status,
                "message": r.message,
                "response_time_ms": r.response_time_ms,
                "details": r.details,
            }
            for r in results
        ],
    }
