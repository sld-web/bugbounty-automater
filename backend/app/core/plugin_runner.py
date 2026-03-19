"""Plugin runner for executing security tools in Docker containers."""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import docker
from docker.errors import DockerException, NotFound

from app.config import get_settings
from app.models.plugin_run import PluginRun, PluginStatus, PermissionLevel

logger = logging.getLogger(__name__)
settings = get_settings()


class PluginRunner:
    """Execute security tool plugins in isolated Docker containers."""

    def __init__(self):
        self.docker_client = None
        self._init_docker()

    def _init_docker(self):
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

    async def run_plugin(
        self,
        plugin_name: str,
        target: str,
        params: dict | None = None,
        timeout_seconds: int = 3600,
        network: str | None = None,
    ) -> PluginRun:
        """Run a plugin against a target."""
        params = params or {}
        manifest = self._get_plugin_manifest(plugin_name)

        plugin_run = PluginRun(
            plugin_name=plugin_name,
            plugin_version=manifest.get("version") if manifest else None,
            target_id=target,
            permission_level=PermissionLevel(
                manifest.get("permission_level", "SAFE")
                if manifest
                else "SAFE"
            ),
            params=params,
            container_image=self._get_plugin_image(plugin_name),
        )
        plugin_run.mark_running()

        if not self.docker_client:
            return await self._run_mock(plugin_run, target, params)

        try:
            container = await self._run_container(
                plugin_name=plugin_name,
                target=target,
                params=params,
                timeout_seconds=timeout_seconds,
                network=network or settings.plugin_network,
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

        return plugin_run

    async def _run_container(
        self,
        plugin_name: str,
        target: str,
        params: dict,
        timeout_seconds: int,
        network: str,
    ) -> docker.models.containers.Container:
        """Run a Docker container for the plugin."""
        plugin_dir = self._get_plugin_dir(plugin_name)
        dockerfile = plugin_dir / "Dockerfile"

        image_name = self._get_plugin_image(plugin_name)

        try:
            self.docker_client.images.get(image_name)
        except NotFound:
            logger.info(f"Building image {image_name}...")
            try:
                self.docker_client.images.build(
                    path=str(plugin_dir),
                    tag=image_name,
                    rm=True,
                )
            except DockerException as e:
                logger.warning(f"Could not build image: {e}")

        env = [f"TARGET={target}", f"PARAMS={json.dumps(params)}"]

        command = f"python /app/run.py --target {target}"

        try:
            container = self.docker_client.containers.run(
                image=image_name,
                command=command,
                environment=env,
                network=network,
                remove=False,
                detach=True,
                stdout=True,
                stderr=True,
            )
            return container
        except DockerException as e:
            raise RuntimeError(f"Failed to start container: {e}")

    async def _wait_for_container(
        self,
        container: docker.models.containers.Container,
        timeout_seconds: int,
    ) -> dict:
        """Wait for container to complete and return results."""
        result = {"exit_code": 0, "stdout": "", "stderr": "", "results": {}}

        try:
            container.wait(timeout=timeout_seconds)
            result["stdout"] = container.logs(stdout=True, stderr=False).decode()
            result["stderr"] = container.logs(stdout=False, stderr=True).decode()
        except Exception as e:
            result["exit_code"] = -1
            result["stderr"] = str(e)

        try:
            container.remove(force=True)
        except Exception:
            pass

        return result

    async def _run_mock(
        self,
        plugin_run: PluginRun,
        target: str,
        params: dict,
    ) -> PluginRun:
        """Run in mock mode when Docker is unavailable."""
        await asyncio.sleep(0.5)

        mock_results = {
            "subdomains": [
                f"www.{target}",
                f"api.{target}",
                f"cdn.{target}",
            ],
            "status": "completed",
        }

        plugin_run.mark_completed(exit_code=0, results=mock_results)
        plugin_run.stdout = json.dumps(mock_results, indent=2)

        return plugin_run

    async def cancel_plugin(self, container_id: str) -> bool:
        """Cancel a running plugin by stopping its container."""
        if not self.docker_client:
            return False

        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            return True
        except NotFound:
            return False
        except DockerException as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
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

    def list_available_plugins(self) -> list[str]:
        """List available plugins from plugins directory."""
        plugins = []
        if settings.plugins_dir.exists():
            for item in settings.plugins_dir.iterdir():
                if item.is_dir() and (item / "plugin.json").exists():
                    plugins.append(item.name)
        return sorted(plugins)
