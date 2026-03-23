"""Coverage dashboard API endpoints."""
from fastapi import APIRouter, Query

router = APIRouter(prefix="/coverage", tags=["coverage"])


class CoverageStats(BaseModel):
    """Coverage statistics for a target."""
    from pydantic import BaseModel


class FlowCardCoverage(BaseModel):
    """Coverage status for flow cards."""
    from pydantic import BaseModel


@router.get("/{target_id}")
async def get_target_coverage(target_id: str) -> dict:
    """Get coverage statistics for a target."""
    return {
        "target_id": target_id,
        "total_cards": 0,
        "completed_cards": 0,
        "pending_cards": 0,
        "coverage_percentage": 0,
        "categories": {
            "recon": {"total": 0, "completed": 0},
            "discovery": {"total": 0, "completed": 0},
            "attack": {"total": 0, "completed": 0},
            "verification": {"total": 0, "completed": 0},
        },
    }


@router.get("/{target_id}/missing")
async def get_missing_coverage(target_id: str) -> dict:
    """Get list of missing coverage areas."""
    return {
        "target_id": target_id,
        "missing_areas": [
            {"category": "attack", "card_type": "sql_injection"},
            {"category": "attack", "card_type": "xss"},
            {"category": "attack", "card_type": "idor"},
        ],
    }


@router.get("/{target_id}/dashboard")
async def get_coverage_dashboard(target_id: str) -> dict:
    """Get comprehensive coverage dashboard data."""
    return {
        "target_id": target_id,
        "summary": {
            "total_flow_cards": 0,
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "coverage_percentage": 0,
        },
        "by_category": {
            "recon": {
                "name": "Reconnaissance",
                "cards": [],
                "coverage": 0,
            },
            "discovery": {
                "name": "Discovery",
                "cards": [],
                "coverage": 0,
            },
            "attack": {
                "name": "Attack Testing",
                "cards": [],
                "coverage": 0,
            },
            "verification": {
                "name": "Verification",
                "cards": [],
                "coverage": 0,
            },
        },
        "severity_breakdown": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,
        },
        "recommendations": [],
    }
