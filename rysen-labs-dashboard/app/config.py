from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_APPS_CONFIG = BASE_DIR / "config" / "apps.yml"


class Settings(BaseModel):
    host_label: str = "rysen-labs"
    server_ip: str = "192.168.50.42"
    apps_config_path: Path = DEFAULT_APPS_CONFIG
    refresh_seconds: int = 30
    docker_socket_path: str = "unix://var/run/docker.sock"


class AppCard(BaseModel):
    name: str
    status: str = "unavailable"
    url: str
    description: str
    category: str
    container_names: list[str] = Field(default_factory=list)


def _coerce_card(raw: dict[str, Any]) -> AppCard:
    return AppCard(
        name=str(raw["name"]),
        status=str(raw.get("status", "unavailable")),
        url=str(raw["url"]),
        description=str(raw["description"]),
        category=str(raw["category"]),
        container_names=[str(item) for item in raw.get("container_names", [])],
    )


@lru_cache
def get_settings() -> Settings:
    return Settings(
        host_label=os.getenv("HOST_LABEL", "rysen-labs"),
        server_ip=os.getenv("SERVER_IP", "192.168.50.42"),
        refresh_seconds=int(os.getenv("REFRESH_SECONDS", "30")),
    )


def load_app_cards(path: Path | None = None) -> list[AppCard]:
    config_path = path or get_settings().apps_config_path
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    apps = payload.get("applications", [])
    if not isinstance(apps, list):
        raise ValueError("applications must be a list")

    return [_coerce_card(item) for item in apps]
