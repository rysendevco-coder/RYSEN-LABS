from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError
import yaml

from app.config import Settings
from app.models.schemas import (
    ProjectConfig,
    ProjectSprintSyncSummary,
    SprintTaskStatus,
    SprintUpdateFile,
    SprintUpdatePayload,
    SprintUpdateRecord,
    SprintUpdateRecommendation,
)


class SprintSyncError(ValueError):
    pass


def _load_structured_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() == ".json":
            payload = json.load(handle)
        else:
            payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise SprintSyncError("update file must contain a mapping/object")
    return payload


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=False)


def _stable_update_id(payload: dict[str, Any]) -> str:
    explicit = payload.get("update_id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    sprint_update = payload.get("sprint_update", payload)
    canonical = json.dumps(sprint_update, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _normal_update_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if "sprint_update" in payload:
        return payload
    return {"update_id": payload.get("update_id"), "sprint_update": payload}


def _read_yaml_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    except OSError as exc:
        raise SprintSyncError(f"Could not read {label} file at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SprintSyncError(f"{label} file must contain a YAML mapping")
    return payload


def _load_projects(path: Path) -> dict[str, ProjectConfig]:
    payload = _read_yaml_mapping(path, "projects")
    raw_projects = payload.get("projects", [])
    if not isinstance(raw_projects, list):
        raise SprintSyncError("projects.yaml field 'projects' must be a list")
    projects: dict[str, ProjectConfig] = {}
    for raw_project in raw_projects:
        project = ProjectConfig.model_validate(raw_project)
        projects[project.id] = project
    return projects


def _tasks_by_id(sprint_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = sprint_payload.get("tasks", [])
    if not isinstance(tasks, list):
        raise SprintSyncError("current_sprint.yaml field 'tasks' must be a list")
    return {task["id"]: task for task in tasks if isinstance(task, dict) and isinstance(task.get("id"), str)}


def _find_checkpoint(task: dict[str, Any], checkpoint_id: str) -> dict[str, Any]:
    checkpoints = task.get("checkpoints") or []
    if not isinstance(checkpoints, list):
        raise SprintSyncError(f"Task '{task.get('id')}' checkpoints must be a list")
    for checkpoint in checkpoints:
        if isinstance(checkpoint, dict) and checkpoint.get("id") == checkpoint_id:
            return checkpoint
    raise SprintSyncError(f"Checkpoint '{checkpoint_id}' was not found on task '{task.get('id')}'")


def _validate_checkpoint_totals(sprint_payload: dict[str, Any]) -> None:
    for task in _tasks_by_id(sprint_payload).values():
        checkpoints = task.get("checkpoints") or []
        if not checkpoints:
            continue
        if not isinstance(checkpoints, list):
            raise SprintSyncError(f"Task '{task.get('id')}' checkpoints must be a list")
        checkpoint_points = sum(int(checkpoint.get("points", 0)) for checkpoint in checkpoints if isinstance(checkpoint, dict))
        if checkpoint_points != int(task.get("points", 0)):
            raise SprintSyncError(
                f"Task '{task.get('id')}' checkpoint points ({checkpoint_points}) must sum to task points ({task.get('points')})",
            )


def _recommendation_status(update: SprintUpdatePayload) -> SprintTaskStatus | None:
    recommendation = update.recommendation
    if recommendation is None:
        return None
    if isinstance(recommendation, SprintUpdateRecommendation):
        return recommendation.status
    if isinstance(recommendation, dict):
        raw_status = recommendation.get("status")
        return SprintTaskStatus(raw_status) if raw_status is not None else None
    if isinstance(recommendation, str) and recommendation.strip():
        return SprintTaskStatus(recommendation.strip())
    return None


def _evidence_mapping(update: SprintUpdatePayload) -> dict[str, str]:
    evidence = update.evidence
    if evidence is None:
        return {}
    if isinstance(evidence, str):
        return {"other": evidence}
    if hasattr(evidence, "model_dump"):
        return {
            str(key): str(value)
            for key, value in evidence.model_dump(exclude_none=True).items()
            if value is not None and str(value).strip()
        }
    if isinstance(evidence, dict):
        return {
            str(key): str(value)
            for key, value in evidence.items()
            if value is not None and str(value).strip()
        }
    return {}


def _validate_completion_evidence(update: SprintUpdatePayload, status: SprintTaskStatus | None) -> None:
    if status != SprintTaskStatus.DONE:
        return
    evidence = _evidence_mapping(update)
    if not evidence:
        raise SprintSyncError("completion updates require objective validation evidence")
    validation = evidence.get("validation", "").strip().lower()
    if validation in {"no validation command configured.", "no validation command configured"}:
        raise SprintSyncError("completion updates require a real validation command or test evidence")
    if validation.startswith("skipped by"):
        raise SprintSyncError("completion updates cannot use skipped validation as evidence")


def _source_commit_sha(update: SprintUpdatePayload) -> str | None:
    evidence = _evidence_mapping(update)
    commit = evidence.get("commit")
    return commit.strip() if commit and commit.strip() else None


def _registered_projects(settings: Settings) -> dict[str, ProjectConfig]:
    return _load_projects(settings.projects_config_path)


def _archive_path(directory: Path, update_id: str, source: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    clean_id = "".join(char for char in update_id if char.isalnum() or char in {"-", "_"}) or "update"
    candidate = directory / f"{clean_id}-{source.name}"
    if not candidate.exists():
        return candidate
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return directory / f"{clean_id}-{stamp}-{source.name}"


class SprintUpdateInboxService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_dir = settings.sprint_updates_dir
        self.pending_dir = self.base_dir / "pending"
        self.processed_dir = self.base_dir / "processed"
        self.rejected_dir = self.base_dir / "rejected"

    def pending_files(self) -> list[Path]:
        if not self.pending_dir.exists():
            return []
        return sorted(
            path
            for path in self.pending_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml", ".json"}
        )

    def processed_update_ids(self) -> set[str]:
        ids: set[str] = set()
        if not self.processed_dir.exists():
            return ids
        for path in self.processed_dir.iterdir():
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml", ".json"}:
                try:
                    ids.add(_stable_update_id(_load_structured_file(path)))
                except (OSError, SprintSyncError, ValueError, yaml.YAMLError, json.JSONDecodeError):
                    continue
        return ids

    def _parse_update(self, path: Path) -> tuple[str, SprintUpdatePayload, SprintTaskStatus | None]:
        raw = _load_structured_file(path)
        normalized = _normal_update_payload(raw)
        update_id = _stable_update_id(normalized)
        try:
            parsed = SprintUpdateFile.model_validate(normalized)
        except ValidationError as exc:
            raise SprintSyncError(f"Invalid sprint_update schema: {exc.errors()[0]['msg']}") from exc

        update = parsed.sprint_update
        recommended_status = _recommendation_status(update)
        _validate_completion_evidence(update, recommended_status)
        projects = _registered_projects(self.settings)
        if update.project not in projects:
            raise SprintSyncError(f"Unknown project '{update.project}'")
        return update_id, update, recommended_status

    def validate_update(self, path: Path) -> tuple[str, SprintUpdatePayload, SprintTaskStatus | None]:
        update_id, update, recommended_status = self._parse_update(path)
        if update.activity_only:
            return update_id, update, recommended_status
        sprint_payload = _read_yaml_mapping(self.settings.current_sprint_config_path, "current sprint")
        _validate_checkpoint_totals(sprint_payload)
        tasks = _tasks_by_id(sprint_payload)
        task = tasks.get(update.task)
        if task is None:
            raise SprintSyncError(f"Unknown task '{update.task}'")
        if task.get("project") != update.project:
            raise SprintSyncError(f"Task '{update.task}' does not belong to project '{update.project}'")
        if update.checkpoint:
            _find_checkpoint(task, update.checkpoint)
        if recommended_status is None:
            raise SprintSyncError("recommendation.status is required")
        return update_id, update, recommended_status

    def process_file(self, path: Path, *, apply: bool) -> SprintUpdateRecord:
        source = path.resolve(strict=False)
        try:
            update_id, update, recommended_status = self.validate_update(source)
            duplicate = update_id in self.processed_update_ids()
            record = SprintUpdateRecord(
                update_id=update_id,
                project=update.project,
                task=update.task,
                checkpoint=update.checkpoint,
                result=update.result,
                recommended_status=recommended_status,
                activity_only=update.activity_only,
                source_commit_sha=_source_commit_sha(update),
                applied=False,
                already_processed=duplicate,
                source_file=str(source),
            )
            if apply and not duplicate and not update.activity_only:
                self._apply_status(update, recommended_status)
                record.applied = True
            if apply:
                record.archived_file = str(self._archive(source, self.processed_dir, update_id))
                record.processed_at = datetime.now(timezone.utc)
            return record
        except (OSError, SprintSyncError, ValidationError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
            update_id = self._safe_update_id_for_failed_file(source)
            record = SprintUpdateRecord(
                update_id=update_id,
                project="unknown",
                task="unknown",
                result="rejected",
                validation_error=str(exc),
                source_file=str(source),
            )
            if apply:
                record.archived_file = str(self._archive(source, self.rejected_dir, update_id))
                record.processed_at = datetime.now(timezone.utc)
            return record

    def process_all(self, *, apply: bool) -> list[SprintUpdateRecord]:
        return [self.process_file(path, apply=apply) for path in self.pending_files()]

    def recent_processed_updates(self, limit: int = 6) -> list[SprintUpdateRecord]:
        if not self.processed_dir.exists():
            return []
        records: list[SprintUpdateRecord] = []
        files = sorted(
            (path for path in self.processed_dir.iterdir() if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in files:
            if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
                continue
            try:
                update_id, update, recommended_status = self.validate_update(path)
            except (OSError, SprintSyncError, ValidationError, ValueError, yaml.YAMLError, json.JSONDecodeError):
                continue
            records.append(
                SprintUpdateRecord(
                    update_id=update_id,
                    project=update.project,
                    task=update.task,
                    checkpoint=update.checkpoint,
                    result=update.result,
                    recommended_status=recommended_status,
                    activity_only=update.activity_only,
                    source_commit_sha=_source_commit_sha(update),
                    applied=not update.activity_only,
                    source_file=str(path),
                    archived_file=str(path),
                    processed_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
                ),
            )
            if len(records) >= limit:
                break
        return records

    def project_freshness(self, project_ids: list[str]) -> list[ProjectSprintSyncSummary]:
        updates = self.recent_processed_updates(limit=500)
        summaries: list[ProjectSprintSyncSummary] = []
        for project_id in project_ids:
            project_updates = [update for update in updates if update.project == project_id]
            latest = project_updates[0] if project_updates else None
            summaries.append(
                ProjectSprintSyncSummary(
                    project=project_id,
                    last_update_time=latest.processed_at if latest else None,
                    last_processed_checkpoint=latest.checkpoint if latest else None,
                    latest_verified_status=latest.recommended_status if latest else None,
                    latest_source_commit_sha=latest.source_commit_sha if latest else None,
                    update_count=len(project_updates),
                ),
            )
        return summaries

    def _apply_status(self, update: SprintUpdatePayload, status: SprintTaskStatus) -> None:
        sprint_payload = _read_yaml_mapping(self.settings.current_sprint_config_path, "current sprint")
        before_points = _total_points(sprint_payload)
        _validate_checkpoint_totals(sprint_payload)
        task = _tasks_by_id(sprint_payload)[update.task]
        target = _find_checkpoint(task, update.checkpoint) if update.checkpoint else task
        target["status"] = status.value
        _validate_checkpoint_totals(sprint_payload)
        if _total_points(sprint_payload) != before_points:
            raise SprintSyncError("point totals changed unexpectedly")
        _write_yaml(self.settings.current_sprint_config_path, sprint_payload)

    def _archive(self, source: Path, directory: Path, update_id: str) -> Path:
        destination = _archive_path(directory, update_id, source)
        if source.exists():
            shutil.move(str(source), str(destination))
        return destination

    def _safe_update_id_for_failed_file(self, path: Path) -> str:
        try:
            return _stable_update_id(_normal_update_payload(_load_structured_file(path)))
        except (OSError, SprintSyncError, ValueError, yaml.YAMLError, json.JSONDecodeError):
            return hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]


def _total_points(sprint_payload: dict[str, Any]) -> int:
    return sum(int(task.get("points", 0)) for task in _tasks_by_id(sprint_payload).values())
