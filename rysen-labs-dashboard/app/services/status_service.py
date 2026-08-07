from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.config import Settings
from app.models.schemas import ApplicationCard, DashboardStatus, ServerInfo
from app.services.app_registry import AppRegistry
from app.services.docker_service import DockerService
from app.services.git_service import GitRepositoryService
from app.services.health_checks import check_applications
from app.services.sprint_service import SprintService
from app.services.system_metrics import collect_system_metrics


class StatusService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.registry = AppRegistry(settings.apps_config_path)
        self.docker = DockerService(settings)
        self.git = GitRepositoryService(settings)
        self.sprint = SprintService(settings)

    async def dashboard_status(self) -> DashboardStatus:
        apps, config_errors = self.registry.load()
        docker_snapshot = self.docker.snapshot()
        repositories, repository_errors = await asyncio.to_thread(self.git.snapshot)
        config_errors.extend(repository_errors)
        sprint = await asyncio.to_thread(self.sprint.load_sprint)
        config_errors.extend(sprint.config_errors)
        system = collect_system_metrics()
        health = await check_applications(
            apps,
            docker_snapshot,
            self.settings.enable_service_health_checks,
        )
        cards = [
            ApplicationCard(
                id=app.id,
                name=app.name,
                description=app.description,
                category=app.category,
                icon=app.icon,
                url=app.url,
                expected_port=app.expected_port,
                enabled=app.enabled,
                display_order=app.display_order,
                health=app_health,
            )
            for app, app_health in zip(apps, health, strict=True)
        ]
        return DashboardStatus(
            server=ServerInfo(
                label=self.settings.host_label,
                ip=self.settings.server_ip,
                safe_mode=self.settings.safe_mode,
            ),
            system=system,
            docker=docker_snapshot,
            applications=cards,
            repositories=repositories,
            sprint=sprint,
            generated_at=datetime.now(timezone.utc),
            update_interval_seconds=self.settings.update_interval_seconds,
            config_errors=config_errors,
        )
