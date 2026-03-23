"""Settings API endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings as get_config
from app.external_config import get_external_apis

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    app_name: str
    app_version: str
    frontend_url: str
    debug: bool
    log_level: str
    database_url: str
    docker_socket: str
    plugin_network: str
    openai_api_key_configured: bool
    shodan_api_key_configured: bool
    github_token_configured: bool
    slack_configured: bool


class UpdateSettingsRequest(BaseModel):
    debug: Optional[bool] = None
    log_level: Optional[str] = None
    frontend_url: Optional[str] = None


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """Get current application settings."""
    settings = get_config()
    external = get_external_apis()
    
    db_url = settings.database_url
    if "@" in db_url:
        db_url = db_url.split("@")[-1]
    
    return SettingsResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        frontend_url=settings.frontend_url,
        debug=settings.debug,
        log_level=settings.log_level,
        database_url=db_url,
        docker_socket=settings.docker_socket,
        plugin_network=settings.plugin_network,
        openai_api_key_configured=bool(external.openai_api_key),
        shodan_api_key_configured=bool(external.shodan_api_key),
        github_token_configured=bool(external.github_token),
        slack_configured=bool(external.slack_bot_token),
    )


@router.patch("", response_model=SettingsResponse)
async def update_settings(request: UpdateSettingsRequest):
    """Update application settings (runtime only, not persisted)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Settings update not yet implemented. Use .env file for permanent changes.",
    )
