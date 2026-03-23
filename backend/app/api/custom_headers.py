"""Custom headers injection API endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.custom_headers_service import get_headers_service

router = APIRouter(prefix="/headers", tags=["custom-headers"])


class HeaderCreateRequest(BaseModel):
    """Request to add a custom header."""
    name: str
    value: str
    source: str = "credential"


class HeadersInjectRequest(BaseModel):
    """Request to inject headers from credentials."""
    credential_type: str
    credential_data: dict
    program_config: Optional[dict] = None


@router.post("")
async def add_custom_header(
    name: str = Query(..., description="Header name"),
    value: str = Query(..., description="Header value"),
    source: str = Query("credential", description="Header source"),
) -> dict:
    """Add a custom header for injection."""
    service = get_headers_service()
    service.add_header(name, value, source)
    
    return {
        "message": f"Header '{name}' added",
        "header": name,
        "source": source,
    }


@router.delete("/{header_name}")
async def remove_custom_header(header_name: str) -> dict:
    """Remove a custom header."""
    service = get_headers_service()
    removed = service.remove_header(header_name)
    
    if not removed:
        raise HTTPException(status_code=404, detail=f"Header '{header_name}' not found")
    
    return {"message": f"Header '{header_name}' removed"}


@router.get("")
async def list_custom_headers() -> dict:
    """List all custom headers."""
    service = get_headers_service()
    headers = service.get_all_headers()
    
    return {
        "headers": [{"name": k, "value": v} for k, v in headers.items()],
        "count": len(headers),
    }


@router.delete("")
async def clear_headers(source: Optional[str] = Query(None)) -> dict:
    """Clear all headers, optionally filtered by source."""
    service = get_headers_service()
    count = service.clear_headers(source)
    
    return {
        "message": f"Cleared {count} headers",
        "count": cleared if (cleared := count) else 0,
    }


@router.post("/inject")
async def inject_authentication_headers(request: HeadersInjectRequest) -> dict:
    """Generate authentication headers from credential data."""
    service = get_headers_service()
    
    headers = service.inject_authentication_headers(
        credential_type=request.credential_type,
        credential_data=request.credential_data,
        program_config=request.program_config,
    )
    
    return {
        "credential_type": request.credential_type,
        "headers": headers,
        "count": len(headers),
    }


@router.get("/config")
async def get_injection_config() -> dict:
    """Get header injection configuration."""
    service = get_headers_service()
    return service.get_injection_config()


@router.post("/policy")
async def apply_policy_headers(
    headers: dict[str, str],
    source: str = Query("policy", description="Source identifier"),
) -> dict:
    """Apply headers from a program policy configuration."""
    service = get_headers_service()
    service.apply_headers_from_policy(headers, source)
    
    return {
        "message": f"Applied {len(headers)} policy headers",
        "headers": headers,
    }
