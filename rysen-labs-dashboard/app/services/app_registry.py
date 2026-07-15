from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError
import yaml

from app.models.schemas import AppConfig, AppHealthState


logger = logging.getLogger(__name__)


class AppRegistryError(ValueError):
    pass


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")


def _coerce_legacy_card(raw: dict[str, Any], index: int) -> dict[str, Any]:
    container_names = raw.get("container_names") or []
    container_name = raw.get("container_name")
    if container_name is None and container_names:
        container_name = str(container_names[0])

    status = raw.get("status", "configured")
    if status == "stopped":
        status = AppHealthState.CONTAINER_STOPPED
    elif status in {"healthy", "degraded", "unavailable"}:
        status = AppHealthState(status)
    else:
        status = AppHealthState.CONFIGURED

    name = str(raw.get("name", f"Application {index + 1}"))
    return {
        "id": raw.get("id") or _slug(name),
        "name": name,
        "description": raw.get("description", ""),
        "category": raw.get("category", "Apps"),
        "icon": raw.get("icon", "square"),
        "url": raw.get("url", ""),
        "internal_health_url": raw.get("internal_health_url"),
        "container_name": container_name,
        "expected_port": raw.get("expected_port"),
        "enabled": raw.get("enabled", True),
        "health_check_enabled": raw.get("health_check_enabled", bool(raw.get("internal_health_url"))),
        "timeout_seconds": raw.get("timeout_seconds", 2.0),
        "display_order": raw.get("display_order", index + 1),
        "configured_status": status,
    }


class AppRegistry:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> tuple[list[AppConfig], list[str]]:
        errors: list[str] = []
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
        except OSError as exc:
            message = f"Could not read apps configuration at {self.path}: {exc}"
            logger.error("apps_config_read_failed", extra={"event": "apps_config_read_failed"})
            return [], [message]

        apps = payload.get("applications", [])
        if not isinstance(apps, list):
            return [], ["apps.yml field 'applications' must be a list"]

        parsed: list[AppConfig] = []
        seen_ids: set[str] = set()
        for index, raw in enumerate(apps):
            if not isinstance(raw, dict):
                errors.append(f"Application entry {index + 1} must be a mapping")
                continue
            try:
                app = AppConfig.model_validate(_coerce_legacy_card(raw, index))
            except ValidationError as exc:
                errors.append(f"Application entry {index + 1} is invalid: {exc.errors()[0]['msg']}")
                continue
            if app.id in seen_ids:
                errors.append(f"Application id '{app.id}' is duplicated")
                continue
            seen_ids.add(app.id)
            parsed.append(app)

        parsed.sort(key=lambda item: (item.display_order, item.name.lower()))
        logger.info("apps_config_loaded", extra={"event": "apps_config_loaded", "app_count": len(parsed)})
        return parsed, errors
