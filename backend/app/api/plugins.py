"""Plugin API endpoints."""
import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings
from app.core.plugin_runner import PluginRunner
from app.schemas.plugin import (
    PluginManifest,
    PluginListResponse,
    PluginRunRequest,
    PluginRunResponse,
)

router = APIRouter(prefix="/plugins", tags=["plugins"])
settings = get_settings()


class PluginInfo(BaseModel):
    name: str
    description: str
    version: str
    permission_level: str
    manifest_path: str


@router.get("", response_model=PluginListResponse)
async def list_plugins():
    """List all available plugins."""
    runner = PluginRunner()
    plugin_list = runner.list_available_plugins()

    plugins = []
    for plugin_info in plugin_list:
        plugins.append(PluginManifest(
            name=plugin_info.get("name"),
            version=plugin_info.get("version"),
            permission_level=plugin_info.get("permission_level"),
            description=plugin_info.get("description", ""),
            inputs=plugin_info.get("inputs", {}),
            outputs=plugin_info.get("outputs", {}),
        ))

    return PluginListResponse(
        plugins=plugins,
        total=len(plugins),
    )


@router.get("/{plugin_name}", response_model=PluginManifest)
async def get_plugin(plugin_name: str):
    """Get plugin manifest."""
    runner = PluginRunner()
    manifest = runner._get_plugin_manifest(plugin_name)

    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )

    return PluginManifest(**manifest)


@router.get("/{plugin_name}/logs")
async def get_plugin_logs(
    plugin_name: str,
    run_id: str | None = None,
):
    """Get logs from a plugin run."""
    logs_dir = settings.project_root / "outputs" / plugin_name

    if not logs_dir.exists():
        return {"logs": []}

    logs = []
    if run_id:
        log_file = logs_dir / f"{run_id}.log"
        if log_file.exists():
            with open(log_file) as f:
                logs = f.readlines()
    else:
        for log_file in logs_dir.glob("*.log"):
            with open(log_file) as f:
                logs.append({
                    "run_id": log_file.stem,
                    "lines": f.readlines(),
                })

    return {"logs": logs}


@router.post("/{plugin_name}/run", response_model=PluginRunResponse)
async def run_plugin(
    plugin_name: str,
    run_request: PluginRunRequest,
):
    """Manually trigger a plugin run."""
    from app.database import get_db_context
    from app.models.plugin_run import PluginRun

    runner = PluginRunner()

    available = runner.list_available_plugins()
    available_names = [p["name"] for p in available]
    if plugin_name not in available_names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin {plugin_name} not found",
        )

    async with get_db_context() as db:
        plugin_run = await runner.run_plugin(
            plugin_name=plugin_name,
            target=run_request.target,
            params=run_request.params,
            timeout_seconds=run_request.timeout_seconds,
        )

        return PluginRunResponse(
            id=plugin_run.id,
            plugin_name=plugin_run.plugin_name,
            plugin_version=plugin_run.plugin_version,
            status=plugin_run.status,
            target_id=plugin_run.target_id,
            permission_level=plugin_run.permission_level,
            params=plugin_run.params,
            container_id=plugin_run.container_id,
            container_image=plugin_run.container_image,
            queued_at=plugin_run.queued_at,
            started_at=plugin_run.started_at,
            completed_at=plugin_run.completed_at,
            duration_seconds=plugin_run.duration_seconds,
            exit_code=plugin_run.exit_code,
            error_message=plugin_run.error_message,
            results=plugin_run.results,
            created_at=plugin_run.created_at,
        )
