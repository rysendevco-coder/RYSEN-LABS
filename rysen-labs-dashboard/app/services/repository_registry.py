from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError
import yaml

from app.models.schemas import RepositoryConfig


logger = logging.getLogger(__name__)


class RepositoryRegistry:
    def __init__(self, path: Path, max_repositories: int | None = None):
        self.path = path
        self.max_repositories = max_repositories

    def load(self) -> tuple[list[RepositoryConfig], list[str]]:
        errors: list[str] = []
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
        except OSError as exc:
            message = f"Could not read repositories configuration at {self.path}: {exc}"
            logger.error("repositories_config_read_failed", extra={"event": "repositories_config_read_failed"})
            return [], [message]

        repositories = payload.get("repositories", [])
        if not isinstance(repositories, list):
            return [], ["repositories.yml field 'repositories' must be a list"]

        parsed: list[RepositoryConfig] = []
        seen_ids: set[str] = set()
        for index, raw in enumerate(repositories[: self.max_repositories]):
            if not isinstance(raw, dict):
                errors.append(f"Repository entry {index + 1} must be a mapping")
                continue
            try:
                repository = RepositoryConfig.model_validate(raw)
            except ValidationError as exc:
                errors.append(f"Repository entry {index + 1} is invalid: {exc.errors()[0]['msg']}")
                continue
            if repository.id in seen_ids:
                errors.append(f"Repository id '{repository.id}' is duplicated")
                continue
            seen_ids.add(repository.id)
            parsed.append(repository)

        if self.max_repositories is not None and len(repositories) > self.max_repositories:
            errors.append(f"Repository configuration is limited to {self.max_repositories} entries")

        parsed.sort(key=lambda item: (item.display_order, item.name.lower()))
        logger.info(
            "repositories_config_loaded",
            extra={"event": "repositories_config_loaded", "repository_count": len(parsed)},
        )
        return parsed, errors
