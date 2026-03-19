"""Docker utility functions."""
import logging
from typing import Any

import docker
from docker.errors import DockerException

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DockerUtils:
    """Docker utility functions."""

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize Docker client."""
        try:
            self.client = docker.DockerClient(
                base_url=settings.docker_socket
            )
            self.client.ping()
        except DockerException as e:
            logger.warning(f"Docker not available: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Docker is available."""
        return self.client is not None

    def get_network(self, network_name: str) -> Any | None:
        """Get or create a Docker network."""
        if not self.client:
            return None

        try:
            return self.client.networks.get(network_name)
        except DockerException:
            try:
                return self.client.networks.create(
                    network_name,
                    driver="bridge",
                    check_duplicate=True,
                )
            except DockerException as e:
                logger.error(f"Failed to create network: {e}")
                return None

    def build_image(
        self,
        path: str,
        tag: str,
        buildargs: dict | None = None,
    ) -> bool:
        """Build a Docker image."""
        if not self.client:
            return False

        try:
            self.client.images.build(
                path=path,
                tag=tag,
                rm=True,
                buildargs=buildargs or {},
            )
            return True
        except DockerException as e:
            logger.error(f"Failed to build image {tag}: {e}")
            return False

    def pull_image(self, image: str) -> bool:
        """Pull a Docker image."""
        if not self.client:
            return False

        try:
            self.client.images.pull(image)
            return True
        except DockerException as e:
            logger.error(f"Failed to pull image {image}: {e}")
            return False

    def list_containers(self, all_containers: bool = False) -> list[dict]:
        """List Docker containers."""
        if not self.client:
            return []

        try:
            containers = self.client.containers.list(all=all_containers)
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else c.image.id,
                    "status": c.status,
                    "created": c.attrs.get("Created"),
                }
                for c in containers
            ]
        except DockerException as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    def cleanup_containers(self, prefix: str = "bugbounty-") -> int:
        """Remove containers with a specific prefix."""
        if not self.client:
            return 0

        count = 0
        try:
            containers = self.client.containers.list(all=True)
            for container in containers:
                if container.name.startswith(prefix):
                    container.remove(force=True)
                    count += 1
        except DockerException as e:
            logger.error(f"Failed to cleanup containers: {e}")

        return count
