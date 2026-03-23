"""Application configuration from environment variables."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Bug Bounty Automator"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = "postgresql+asyncpg://bugbounty:bugbounty@localhost:5432/bugbounty_db"
    database_url_sync: str = "postgresql://bugbounty:bugbounty@localhost:5432/bugbounty_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Docker
    docker_socket: str = "unix:///var/run/docker.sock"
    plugin_network: str = "bugbounty_plugins"

    # Worker
    worker_concurrency: int = 5
    worker_timeout: int = 3600

    # Encryption
    encryption_key: str = ""

    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent.parent
    
    @property
    def plugins_dir(self) -> Path:
        return self.project_root / "plugins"
    
    @property
    def external_api_config_path(self) -> Path:
        return Path(__file__).parent / "api_keys.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
