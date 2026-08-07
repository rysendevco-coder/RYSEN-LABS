from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl, field_validator


class AppHealthState(StrEnum):
    CONFIGURED = "configured"
    DISABLED = "disabled"
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CONTAINER_RUNNING = "container_running"
    CONTAINER_STOPPED = "container_stopped"
    UNAVAILABLE = "unavailable"


class RepositoryStatusClass(StrEnum):
    HEALTHY = "healthy"
    DIRTY = "dirty"
    AHEAD = "ahead"
    BEHIND = "behind"
    DIVERGED = "diverged"
    CONFLICTED = "conflicted"
    DETACHED = "detached"
    MISSING = "missing"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


class SprintTaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class ProjectSprintStatus(StrEnum):
    ON_TRACK = "On Track"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETE = "Complete"


class Usage(BaseModel):
    percent: float | None
    used_gb: float | None = None
    total_gb: float | None = None


class SystemMetrics(BaseModel):
    hostname: str
    uptime_seconds: int | None
    uptime_human: str
    cpu_percent: float | None
    load_average: list[float] | None
    memory: Usage
    disk: Usage
    cpu_temperature_c: float | None
    unavailable: list[str] = Field(default_factory=list)


class ContainerStatus(BaseModel):
    name: str
    status: str
    health: str
    image: str


class DockerSnapshot(BaseModel):
    enabled: bool
    available: bool
    containers: list[ContainerStatus] = Field(default_factory=list)
    error: str | None = None


class AppConfig(BaseModel):
    id: str
    name: str
    description: str
    category: str = "Apps"
    icon: str = "square"
    url: str
    internal_health_url: str | None = None
    container_name: str | None = None
    expected_port: int | None = Field(default=None, ge=1, le=65535)
    enabled: bool = True
    health_check_enabled: bool = False
    timeout_seconds: float = Field(default=2.0, gt=0, le=15)
    display_order: int = 100
    configured_status: AppHealthState = AppHealthState.CONFIGURED

    @field_validator("id")
    @classmethod
    def id_is_slug(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("id cannot be empty")
        if any(char for char in cleaned if not (char.isalnum() or char in {"-", "_"})):
            raise ValueError("id must contain only letters, numbers, hyphens, or underscores")
        return cleaned

    @field_validator("url", "internal_health_url")
    @classmethod
    def validate_http_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        HttpUrl(value)
        return value


class RepositoryConfig(BaseModel):
    id: str
    name: str
    description: str = ""
    path: Path
    category: str = "Repositories"
    expected_remote: str | None = "origin"
    default_branch: str | None = "develop"
    enabled: bool = True
    display_order: int = 100

    @field_validator("id")
    @classmethod
    def id_is_slug(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("id cannot be empty")
        if any(char for char in cleaned if not (char.isalnum() or char in {"-", "_"})):
            raise ValueError("id must contain only letters, numbers, hyphens, or underscores")
        return cleaned

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: Path) -> Path:
        return value.expanduser().resolve(strict=False)


class ProjectConfig(BaseModel):
    id: str
    name: str
    short_name: str
    description: str = ""
    display_order: int = 100

    @field_validator("id")
    @classmethod
    def id_is_slug(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("id cannot be empty")
        if any(char for char in cleaned if not (char.isalnum() or char in {"-", "_"})):
            raise ValueError("id must contain only letters, numbers, hyphens, or underscores")
        return cleaned


class SprintTask(BaseModel):
    id: str
    project: str
    name: str
    description: str
    points: int = Field(ge=0)
    status: SprintTaskStatus
    blocker: str | None = None
    notes: str | None = None

    @field_validator("id", "project")
    @classmethod
    def slug_fields(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("value cannot be empty")
        if any(char for char in cleaned if not (char.isalnum() or char in {"-", "_"})):
            raise ValueError("value must contain only letters, numbers, hyphens, or underscores")
        return cleaned


class TaskCounts(BaseModel):
    todo: int = 0
    in_progress: int = 0
    blocked: int = 0
    done: int = 0


class SprintProgress(BaseModel):
    total_points: int
    completed_points: int
    progress_percentage: float
    task_counts: TaskCounts


class ProjectSprintSummary(BaseModel):
    id: str
    name: str
    short_name: str
    description: str = ""
    status: ProjectSprintStatus
    current_focus: str
    blockers: list[SprintTask] = Field(default_factory=list)
    tasks: list[SprintTask] = Field(default_factory=list)
    progress: SprintProgress
    display_order: int = 100


class SprintRevenueGoal(BaseModel):
    name: str
    description: str


class SprintSummary(BaseModel):
    name: str
    start_date: str
    end_date: str
    date_label: str
    primary_objective: str
    revenue_goal: SprintRevenueGoal
    projects: list[ProjectSprintSummary]
    needs_attention: list[SprintTask]
    progress: SprintProgress
    config_errors: list[str] = Field(default_factory=list)


class RepositoryStatus(BaseModel):
    configured: bool = True
    enabled: bool
    path_exists: bool = False
    valid_git_repository: bool = False
    repository_name: str
    path: str
    category: str = "Repositories"
    current_branch: str | None = None
    detached_head: bool = False
    current_commit_sha: str | None = None
    short_commit_sha: str | None = None
    latest_commit_message: str | None = None
    latest_commit_timestamp: datetime | None = None
    remote_name: str | None = None
    remote_url: str | None = None
    expected_default_branch: str | None = None
    working_tree_clean: bool | None = None
    modified_files: int = 0
    staged_files: int = 0
    untracked_files: int = 0
    conflicted_files: int = 0
    ahead_count: int | None = None
    behind_count: int | None = None
    upstream_branch: str | None = None
    tag_or_version: str | None = None
    last_checked_at: datetime
    warning: str | None = None
    status_class: RepositoryStatusClass
    display_order: int = 100


class AppHealth(BaseModel):
    state: AppHealthState
    http_status: int | None = None
    latency_ms: int | None = None
    last_checked_at: datetime | None = None
    container_state: str | None = None
    error: str | None = None
    source: str = "configuration"


class ApplicationCard(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon: str
    url: str
    expected_port: int | None = None
    enabled: bool
    display_order: int
    health: AppHealth


class ServerInfo(BaseModel):
    label: str
    ip: str
    safe_mode: bool


class DashboardStatus(BaseModel):
    server: ServerInfo
    system: SystemMetrics
    docker: DockerSnapshot
    applications: list[ApplicationCard]
    repositories: list[RepositoryStatus] = Field(default_factory=list)
    sprint: SprintSummary | None = None
    generated_at: datetime
    update_interval_seconds: int
    config_errors: list[str] = Field(default_factory=list)
