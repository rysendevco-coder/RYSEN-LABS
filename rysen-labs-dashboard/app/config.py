from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_APPS_CONFIG = BASE_DIR / "config" / "apps.yml"
DEFAULT_REPOSITORIES_CONFIG = BASE_DIR / "config" / "repositories.yml"
DEFAULT_PROJECTS_CONFIG = BASE_DIR / "roadmap" / "projects.yaml"
DEFAULT_CURRENT_SPRINT_CONFIG = BASE_DIR / "roadmap" / "current_sprint.yaml"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_optional_int(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return int(value)


class Settings(BaseModel):
    host_label: str = "rysen-labs"
    server_ip: str = "192.168.50.42"
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8080
    update_interval_seconds: int = Field(default=30, ge=5, le=3600)
    enable_docker_integration: bool = False
    docker_socket_path: str = "unix://var/run/docker.sock"
    enable_service_health_checks: bool = True
    enable_git_integration: bool = False
    safe_mode: bool = True
    log_level: str = "INFO"
    apps_config_path: Path = DEFAULT_APPS_CONFIG
    repositories_config_path: Path = DEFAULT_REPOSITORIES_CONFIG
    projects_config_path: Path = DEFAULT_PROJECTS_CONFIG
    current_sprint_config_path: Path = DEFAULT_CURRENT_SPRINT_CONFIG
    git_command_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    git_max_repositories: int | None = Field(default=None, gt=0, le=500)
    git_scan_cache_seconds: float = Field(default=15.0, ge=0, le=300)

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    return Settings(
        host_label=os.getenv("HOST_LABEL", "rysen-labs"),
        server_ip=os.getenv("SERVER_IP", "192.168.50.42"),
        dashboard_host=os.getenv("DASHBOARD_HOST", "0.0.0.0"),
        dashboard_port=_env_int("DASHBOARD_PORT", 8080),
        update_interval_seconds=_env_int(
            "DASHBOARD_UPDATE_INTERVAL_SECONDS",
            _env_int("REFRESH_SECONDS", 30),
        ),
        enable_docker_integration=_env_bool("ENABLE_DOCKER_INTEGRATION", False),
        docker_socket_path=os.getenv("DOCKER_SOCKET_PATH", "unix://var/run/docker.sock"),
        enable_service_health_checks=_env_bool("ENABLE_SERVICE_HEALTH_CHECKS", True),
        enable_git_integration=_env_bool("ENABLE_GIT_INTEGRATION", False),
        safe_mode=_env_bool("SAFE_MODE", True),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        apps_config_path=Path(os.getenv("APPS_CONFIG_PATH", str(DEFAULT_APPS_CONFIG))),
        repositories_config_path=Path(
            os.getenv("REPOSITORIES_CONFIG_PATH", str(DEFAULT_REPOSITORIES_CONFIG)),
        ),
        projects_config_path=Path(os.getenv("PROJECTS_CONFIG_PATH", str(DEFAULT_PROJECTS_CONFIG))),
        current_sprint_config_path=Path(
            os.getenv("CURRENT_SPRINT_CONFIG_PATH", str(DEFAULT_CURRENT_SPRINT_CONFIG)),
        ),
        git_command_timeout_seconds=float(os.getenv("GIT_COMMAND_TIMEOUT_SECONDS", "5")),
        git_max_repositories=_env_optional_int("GIT_MAX_REPOSITORIES"),
        git_scan_cache_seconds=float(os.getenv("GIT_SCAN_CACHE_SECONDS", "15")),
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
