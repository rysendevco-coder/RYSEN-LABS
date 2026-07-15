from __future__ import annotations

import logging
from typing import Any

import docker
from docker.errors import DockerException

from app.config import Settings
from app.models.schemas import ContainerStatus, DockerSnapshot


logger = logging.getLogger(__name__)


class DockerService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def snapshot(self) -> DockerSnapshot:
        if not self.settings.enable_docker_integration:
            return DockerSnapshot(enabled=False, available=False, error="Docker integration disabled")

        try:
            client = docker.DockerClient(base_url=self.settings.docker_socket_path)
            containers = client.containers.list(all=True)
        except DockerException as exc:
            logger.warning("docker_unavailable", extra={"event": "docker_unavailable"})
            return DockerSnapshot(enabled=True, available=False, error="Docker socket unavailable")

        logger.info("docker_available", extra={"event": "docker_available", "container_count": len(containers)})
        return DockerSnapshot(
            enabled=True,
            available=True,
            containers=[
                ContainerStatus(
                    name=container.name,
                    status=str(container.status or "unknown"),
                    health=_health_from_attrs(container),
                    image=", ".join(container.image.tags) if container.image.tags else container.image.short_id,
                )
                for container in containers
            ],
        )


def _health_from_attrs(container: Any) -> str:
    health = getattr(container, "attrs", {}).get("State", {}).get("Health", {})
    status = health.get("Status")
    if status:
        return str(status)
    return str(getattr(container, "status", None) or "unknown")
