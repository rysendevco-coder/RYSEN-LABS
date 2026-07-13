from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import docker
from docker.errors import DockerException


logger = logging.getLogger(__name__)


@dataclass
class ContainerStatus:
    name: str
    status: str
    health: str
    image: str


@dataclass
class DockerSnapshot:
    available: bool
    containers: list[ContainerStatus]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "containers": [asdict(container) for container in self.containers],
            "error": self.error,
        }


def _health_from_attrs(container: Any) -> str:
    health = container.attrs.get("State", {}).get("Health", {})
    status = health.get("Status")
    if status:
        return str(status)
    return str(container.status or "unknown")


def collect_docker_status() -> DockerSnapshot:
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
    except DockerException as exc:
        logger.warning("docker_unavailable", exc_info=exc)
        return DockerSnapshot(available=False, containers=[], error="Docker socket unavailable")

    snapshot = [
        ContainerStatus(
            name=container.name,
            status=str(container.status or "unknown"),
            health=_health_from_attrs(container),
            image=", ".join(container.image.tags) if container.image.tags else container.image.short_id,
        )
        for container in containers
    ]
    return DockerSnapshot(available=True, containers=snapshot)


def health_state_for_app(container_names: list[str], snapshot: DockerSnapshot, configured_status: str) -> str:
    valid_states = {"healthy", "degraded", "stopped", "unavailable"}
    if configured_status in valid_states and not container_names:
        return configured_status
    if not container_names:
        return "unavailable"
    if not snapshot.available:
        return "unavailable"

    by_name = {container.name.lower(): container for container in snapshot.containers}
    matched = [by_name.get(name.lower()) for name in container_names]
    present = [container for container in matched if container is not None]
    if not present:
        return "unavailable"
    if any(container.status in {"exited", "dead", "created"} for container in present):
        return "stopped"
    if all(container.status == "running" and container.health in {"running", "healthy"} for container in present):
        return "healthy"
    return "degraded"
