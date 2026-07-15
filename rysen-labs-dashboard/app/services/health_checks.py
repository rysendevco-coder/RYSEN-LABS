from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx

from app.models.schemas import AppConfig, AppHealth, AppHealthState, DockerSnapshot


logger = logging.getLogger(__name__)


def _container_state(app: AppConfig, docker_snapshot: DockerSnapshot) -> str | None:
    if not app.container_name or not docker_snapshot.available:
        return None
    containers = {container.name.lower(): container for container in docker_snapshot.containers}
    container = containers.get(app.container_name.lower())
    if container is None:
        return "missing"
    return container.status


def _state_from_container(state: str | None) -> AppHealthState | None:
    if state is None:
        return None
    if state == "missing":
        return AppHealthState.UNAVAILABLE
    if state == "running":
        return AppHealthState.CONTAINER_RUNNING
    if state in {"exited", "dead", "created"}:
        return AppHealthState.CONTAINER_STOPPED
    return AppHealthState.DEGRADED


async def _http_health(app: AppConfig) -> AppHealth:
    if not app.internal_health_url:
        return AppHealth(state=AppHealthState.UNKNOWN, source="http", error="No health URL configured")

    started = time.perf_counter()
    checked_at = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=app.timeout_seconds, follow_redirects=False) as client:
            response = await client.get(app.internal_health_url)
    except httpx.TimeoutException:
        logger.warning("health_check_timeout", extra={"event": "health_check_timeout", "app_id": app.id})
        return AppHealth(
            state=AppHealthState.UNHEALTHY,
            last_checked_at=checked_at,
            error="Health check timed out",
            source="http",
        )
    except httpx.RequestError:
        logger.warning("health_check_connection_failed", extra={"event": "health_check_connection_failed", "app_id": app.id})
        return AppHealth(
            state=AppHealthState.UNAVAILABLE,
            last_checked_at=checked_at,
            error="Health check connection failed",
            source="http",
        )

    latency_ms = int((time.perf_counter() - started) * 1000)
    if 200 <= response.status_code < 400:
        state = AppHealthState.HEALTHY
    elif 400 <= response.status_code < 500:
        state = AppHealthState.DEGRADED
    else:
        state = AppHealthState.UNHEALTHY
    return AppHealth(
        state=state,
        http_status=response.status_code,
        latency_ms=latency_ms,
        last_checked_at=checked_at,
        source="http",
    )


async def check_application(
    app: AppConfig,
    docker_snapshot: DockerSnapshot,
    service_checks_enabled: bool,
) -> AppHealth:
    checked_at = datetime.now(timezone.utc)
    if not app.enabled:
        return AppHealth(state=AppHealthState.DISABLED, last_checked_at=checked_at, source="configuration")

    container_state = _container_state(app, docker_snapshot)
    container_health = _state_from_container(container_state)

    if service_checks_enabled and app.health_check_enabled:
        health = await _http_health(app)
        health.container_state = container_state
        if container_health == AppHealthState.CONTAINER_STOPPED and health.state == AppHealthState.UNAVAILABLE:
            health.state = AppHealthState.CONTAINER_STOPPED
        return health

    if container_health is not None:
        return AppHealth(
            state=container_health,
            last_checked_at=checked_at,
            container_state=container_state,
            source="docker",
        )

    return AppHealth(state=app.configured_status, last_checked_at=checked_at, source="configuration")


async def check_applications(
    apps: list[AppConfig],
    docker_snapshot: DockerSnapshot,
    service_checks_enabled: bool,
) -> list[AppHealth]:
    return await asyncio.gather(
        *(check_application(app, docker_snapshot, service_checks_enabled) for app in apps),
    )
