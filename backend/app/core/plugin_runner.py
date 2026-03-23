"""Plugin runner for executing security tools in Docker containers with isolation."""
from __future__ import annotations
import asyncio
import json
import logging
import os
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import docker
from docker import DockerClient
from docker.errors import DockerException, NotFound
from docker.types import HostConfig, Resources
from docker.models import containers

from app.config import get_settings
from app.models.plugin_run import PluginRun, PluginStatus, PermissionLevel

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class PluginIsolationConfig:
    """Configuration for container isolation settings."""
    
    network_mode: str = "none"
    mem_limit: str = "256m"
    cpu_period: int = 100000
    cpu_quota: int = 50000
    read_only: bool = True
    cap_drop: Optional[list[str]] = None
    security_opt: Optional[list[str]] = None
    auto_remove: bool = True
    timeout_seconds: int = 300
    
    def __post_init__(self):
        if self.cap_drop is None:
            self.cap_drop = ["ALL"]
        if self.security_opt is None:
            self.security_opt = ["no-new-privileges"]


@dataclass
class ResourceLimits:
    """Resource limits for plugins based on permission level."""
    
    SAFE = PluginIsolationConfig(
        network_mode="none",
        mem_limit="256m",
        cpu_quota=50000,
        timeout_seconds=300,
    )
    
    LIMITED = PluginIsolationConfig(
        network_mode="bridge",
        mem_limit="512m",
        cpu_quota=100000,
        timeout_seconds=600,
    )
    
    DANGEROUS = PluginIsolationConfig(
        network_mode="bridge",
        mem_limit="1g",
        cpu_quota=200000,
        timeout_seconds=3600,
    )


class PluginRunner:
    """Execute security tool plugins in isolated Docker containers."""

    def __init__(self):
        self.docker_client: DockerClient | None = None
        self._init_docker()
        self._network_cache: dict[str, Any] = {}

    def _init_docker(self) -> None:
        """Initialize Docker client."""
        try:
            self.docker_client = docker.DockerClient(
                base_url=settings.docker_socket
            )
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.warning(f"Docker not available: {e}. Running in mock mode.")
            self.docker_client = None

    def _get_plugin_image(self, plugin_name: str) -> str:
        """Get Docker image name for plugin."""
        return f"bugbounty-{plugin_name}:latest"

    def _get_plugin_dir(self, plugin_name: str) -> Path:
        """Get plugin directory path."""
        return settings.plugins_dir / plugin_name

    def _get_plugin_manifest(self, plugin_name: str) -> dict | None:
        """Load plugin manifest."""
        manifest_path = self._get_plugin_dir(plugin_name) / "plugin.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)
        return None

    def _get_isolation_config(self, permission_level: PermissionLevel) -> PluginIsolationConfig:
        """Get isolation config based on permission level."""
        config_map = {
            PermissionLevel.SAFE: ResourceLimits.SAFE,
            PermissionLevel.LIMITED: ResourceLimits.LIMITED,
            PermissionLevel.DANGEROUS: ResourceLimits.DANGEROUS,
        }
        return config_map.get(permission_level, ResourceLimits.SAFE)

    def _ensure_network(self, network_name: str) -> str | None:
        """Ensure a Docker network exists, return its name or None."""
        if not self.docker_client:
            return None
        
        if network_name == "none" or network_name == "bridge":
            return network_name
        
        if network_name in self._network_cache:
            return self._network_cache[network_name]
        
        try:
            network = self.docker_client.networks.get(network_name)
            self._network_cache[network_name] = network_name
            return network_name
        except NotFound:
            try:
                network = self.docker_client.networks.create(
                    name=network_name,
                    driver="bridge",
                    check_duplicate=True,
                )
                self._network_cache[network_name] = network_name
                return network_name
            except DockerException as e:
                logger.warning(f"Could not create network {network_name}: {e}")
                return "bridge"

    def _build_plugin_image(self, plugin_name: str, plugin_dir: Path) -> bool:
        """Build Docker image for a plugin."""
        if not self.docker_client:
            return False
        
        image_name = self._get_plugin_image(plugin_name)
        
        try:
            self.docker_client.images.get(image_name)
            logger.info(f"Image {image_name} already exists")
            return True
        except NotFound:
            pass
        
        dockerfile = plugin_dir / "Dockerfile"
        if not dockerfile.exists():
            logger.error(f"Dockerfile not found for plugin {plugin_name}")
            return False
        
        try:
            logger.info(f"Building image {image_name}...")
            _, logs = self.docker_client.images.build(
                path=str(plugin_dir),
                tag=image_name,
                rm=True,
                pull=True,
            )
            for log in logs:
                if isinstance(log, dict) and "stream" in log:
                    logger.debug(str(log["stream"]).strip())
            logger.info(f"Successfully built image {image_name}")
            return True
        except DockerException as e:
            logger.error(f"Failed to build image {image_name}: {e}")
            return False

    async def run_plugin(
        self,
        plugin_name: str,
        target: str,
        params: dict | None = None,
        timeout_seconds: int = 3600,
        network: str | None = None,
        permission_level: PermissionLevel | None = None,
    ) -> PluginRun:
        """Run a plugin against a target with Docker isolation."""
        params = params or {}
        manifest = self._get_plugin_manifest(plugin_name)
        
        if permission_level is None:
            permission_level = PermissionLevel(
                manifest.get("permission_level", "SAFE")
                if manifest
                else "SAFE"
            )

        plugin_run = PluginRun(
            plugin_name=plugin_name,
            plugin_version=manifest.get("version") if manifest else None,
            target_id=target,
            permission_level=permission_level,
            params=params,
            container_image=self._get_plugin_image(plugin_name),
        )
        plugin_run.mark_running()

        if not self.docker_client:
            logger.info("Docker not available, running in mock mode")
            return await self._run_mock(plugin_run, target, params)

        try:
            container = await self._run_container(
                plugin_name=plugin_name,
                target=target,
                params=params,
                timeout_seconds=timeout_seconds,
                network=network,
                permission_level=permission_level,
            )

            plugin_run.container_id = container.id

            result = await self._wait_for_container(
                container, timeout_seconds
            )

            plugin_run.mark_completed(
                exit_code=result.get("exit_code", 0),
                results=result.get("results", {}),
            )
            plugin_run.stdout = result.get("stdout", "")
            plugin_run.stderr = result.get("stderr", "")

        except asyncio.TimeoutError:
            plugin_run.mark_timeout()
            logger.error(f"Plugin {plugin_name} timed out after {timeout_seconds}s")

        except Exception as e:
            plugin_run.mark_failed(str(e))
            logger.exception(f"Plugin {plugin_name} failed: {e}")
            plugin_run.stdout = str(e)
            plugin_run.stderr = traceback.format_exc()

        return plugin_run

    async def _run_container(
        self,
        plugin_name: str,
        target: str,
        params: dict,
        timeout_seconds: int,
        network: str | None,
        permission_level: PermissionLevel,
    ) -> Any:
        """Run a Docker container for the plugin with isolation settings."""
        plugin_dir = self._get_plugin_dir(plugin_name)
        
        if not self._build_plugin_image(plugin_name, plugin_dir):
            raise RuntimeError(f"Failed to build image for plugin {plugin_name}")

        image_name = self._get_plugin_image(plugin_name)
        isolation_config = self._get_isolation_config(permission_level)
        
        network_mode = network or settings.plugin_network
        if network_mode != "none":
            network_mode = self._ensure_network(network_mode) or "bridge"

        tmp_volume = tempfile.mkdtemp(prefix="bugbounty_")
        os.chmod(tmp_volume, 0o777)
        
        env = {
            "TARGET": target,
            "PARAMS": json.dumps(params),
            "TMPDIR": "/tmp",
        }
        
        env_list = [f"{k}={v}" for k, v in env.items()]

        command = f"python /app/run.py --target {target}"

        host_config = HostConfig(
            version="1.41",
            network_mode=network_mode,
            mem_limit=isolation_config.mem_limit,
            cpu_period=isolation_config.cpu_period,
            cpu_quota=isolation_config.cpu_quota,
            read_only=False,
            cap_drop=isolation_config.cap_drop,
            security_opt=isolation_config.security_opt,
            auto_remove=False,
            tmpfs={
                "/tmp": "size=64M,noexec,nosuid,nodev",
                "/run": "size=16M,noexec,nosuid,nodev",
            },
        )

        try:
            response = self.docker_client.api.create_container(
                image=image_name,
                command=command,
                environment=env_list,
                host_config=host_config,
                detach=True,
                networking_config=self.docker_client.api.create_networking_config({
                    network_mode: self.docker_client.api.create_endpoint_config()
                }) if network_mode and network_mode != "bridge" else None,
            )
            container = self.docker_client.containers.get(response["Id"])
            container.start()
            
            logger.info(
                f"Started container {container.id[:12]} for plugin {plugin_name} "
                f"(network={network_mode}, mem={isolation_config.mem_limit})"
            )
            
            return container
        except DockerException as e:
            raise RuntimeError(f"Failed to start container: {e}")

    async def _wait_for_container(
        self,
        container: Any,
        timeout_seconds: int,
    ) -> dict:
        """Wait for container to complete and return results."""
        result = {"exit_code": 0, "stdout": "", "stderr": "", "results": {}}

        try:
            response = container.wait(timeout=timeout_seconds)
            result["exit_code"] = response.get("StatusCode", 0)
            
            result["stdout"] = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            result["stderr"] = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            
            result["results"] = self._parse_plugin_output(result["stdout"])

        except Exception as e:
            result["exit_code"] = -1
            result["stderr"] = str(e)
            logger.error(f"Error waiting for container {container.id[:12]}: {e}")

        finally:
            try:
                container.remove(force=True)
                logger.debug(f"Removed container {container.id[:12]}")
            except Exception:
                pass

        return result

    def _parse_plugin_output(self, stdout: str) -> dict:
        """Parse JSON output from plugin."""
        try:
            last_line = stdout.strip().split("\n")[-1]
            return json.loads(last_line)
        except (json.JSONDecodeError, IndexError):
            return {"raw_output": stdout[:5000]}

    async def _run_mock(
        self,
        plugin_run: PluginRun,
        target: str,
        params: dict,
    ) -> PluginRun:
        """Run in mock mode when Docker is unavailable."""
        await asyncio.sleep(0.5)

        plugin_name = plugin_run.plugin_name
        mock_results = self._get_mock_results(plugin_name, target, params)

        plugin_run.mark_completed(exit_code=0, results=mock_results)
        plugin_run.stdout = json.dumps(mock_results, indent=2)

        return plugin_run

    def _get_mock_results(self, plugin_name: str, target: str, params: dict) -> dict:
        """Get mock results based on plugin name."""
        
        if plugin_name == "subfinder":
            return {
                "subdomains": [
                    f"www.{target}",
                    f"api.{target}",
                    f"admin.{target}",
                    f"cdn.{target}",
                    f"mail.{target}",
                ],
                "status": "completed",
            }
        
        elif plugin_name == "amass":
            subdomains = params.get("subdomains", [f"www.{target}", f"api.{target}"])
            return {
                "subdomains": subdomains + [f"dev.{target}", f"staging.{target}"],
                "scan_log": f"Amass scan completed for {target}",
                "status": "completed",
            }
        
        elif plugin_name == "nmap":
            return {
                "ports": [
                    {"port": 80, "service": "http", "state": "open"},
                    {"port": 443, "service": "https", "state": "open"},
                    {"port": 22, "service": "ssh", "state": "open"},
                    {"port": 3306, "service": "mysql", "state": "filtered"},
                ],
                "status": "completed",
            }
        
        elif plugin_name == "httpx":
            subdomains = params.get("subdomains", [target])
            return {
                "endpoints": [
                    {"url": f"https://{subdomains[0]}/", "status": 200, "tech": ["nginx", "PHP"]},
                    {"url": f"https://api.{target}/api", "status": 200, "tech": ["nginx", "Node.js"]},
                    {"url": f"https://admin.{target}/login", "status": 200, "tech": ["nginx", "Python"]},
                ],
                "technologies": ["nginx", "PHP", "Node.js", "Python", "MySQL"],
                "status": "completed",
            }
        
        elif plugin_name == "nuclei":
            endpoints = params.get("endpoints", [{"url": f"https://{target}/"}])
            return {
                "findings": [
                    {
                        "type": "missing_security_headers",
                        "severity": "info",
                        "url": endpoints[0].get("url", target) if isinstance(endpoints[0], dict) else target,
                        "description": "Security headers are missing",
                    },
                    {
                        "type": "open_redirect",
                        "severity": "medium",
                        "url": f"https://{target}/redirect?url=http://evil.com",
                        "description": "Open redirect vulnerability found",
                    },
                ],
                "status": "completed",
            }
        
        else:
            return {
                "subdomains": [f"www.{target}", f"api.{target}"],
                "status": "completed",
            }

    async def cancel_plugin(self, container_id: str) -> bool:
        """Cancel a running plugin by stopping its container."""
        if not self.docker_client:
            return False

        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            logger.info(f"Stopped container {container_id[:12]}")
            return True
        except NotFound:
            return False
        except DockerException as e:
            logger.error(f"Failed to stop container {container_id[:12]}: {e}")
            return False

    def get_plugin_status(self, container_id: str) -> str | None:
        """Get current status of a plugin container."""
        if not self.docker_client:
            return None

        try:
            container = self.docker_client.containers.get(container_id)
            return container.status
        except NotFound:
            return None

    def list_available_plugins(self) -> list[dict]:
        """List available plugins with their metadata."""
        plugins = []
        if settings.plugins_dir.exists():
            for item in settings.plugins_dir.iterdir():
                if item.is_dir():
                    manifest = self._get_plugin_manifest(item.name)
                    dockerfile = item / "Dockerfile"
                    plugins.append({
                        "name": item.name,
                        "version": manifest.get("version") if manifest else None,
                        "permission_level": manifest.get("permission_level", "UNKNOWN") if manifest else "UNKNOWN",
                        "description": manifest.get("description", "") if manifest else "",
                        "has_dockerfile": dockerfile.exists(),
                        "has_docker_image": self._check_image_exists(item.name),
                    })
        return sorted(plugins, key=lambda x: x["name"])

    def _check_image_exists(self, plugin_name: str) -> bool:
        """Check if plugin Docker image exists."""
        if not self.docker_client:
            return False
        try:
            self.docker_client.images.get(self._get_plugin_image(plugin_name))
            return True
        except NotFound:
            return False

    def get_plugin_info(self, plugin_name: str) -> dict | None:
        """Get detailed info for a specific plugin."""
        manifest = self._get_plugin_manifest(plugin_name)
        if not manifest:
            return None
        
        return {
            "name": plugin_name,
            "version": manifest.get("version"),
            "permission_level": manifest.get("permission_level", "UNKNOWN"),
            "description": manifest.get("description", ""),
            "inputs": manifest.get("inputs", {}),
            "outputs": manifest.get("outputs", {}),
            "has_dockerfile": (self._get_plugin_dir(plugin_name) / "Dockerfile").exists(),
            "has_docker_image": self._check_image_exists(plugin_name),
        }
