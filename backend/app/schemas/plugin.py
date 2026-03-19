"""Plugin schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.plugin_run import PermissionLevel, PluginStatus


class PluginInput(BaseModel):
    name: str
    type: str = Field(..., pattern="^(string|integer|boolean|array|object)$")
    required: bool = False
    default: any = None
    description: str | None = None


class PluginOutput(BaseModel):
    name: str
    type: str
    description: str | None = None


class PluginManifest(BaseModel):
    name: str
    version: str
    permission_level: PermissionLevel
    description: str
    inputs: dict[str, PluginInput]
    outputs: dict[str, PluginOutput]
    timeout_seconds: int = 3600
    docker_image: str | None = None
    docker_file: str | None = None
    entrypoint: str = "python /app/run.py"
    environment: dict = Field(default_factory=dict)


class PluginRunRequest(BaseModel):
    plugin_name: str
    target: str
    params: dict = Field(default_factory=dict)
    wait_for_completion: bool = True
    timeout_seconds: int = 3600


class PluginRunResponse(BaseModel):
    id: str
    plugin_name: str
    plugin_version: str | None
    status: PluginStatus
    target_id: str
    permission_level: PermissionLevel
    params: dict
    container_id: str | None
    container_image: str | None
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    exit_code: int | None
    error_message: str | None
    results: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class PluginListResponse(BaseModel):
    plugins: list[PluginManifest]
    total: int
