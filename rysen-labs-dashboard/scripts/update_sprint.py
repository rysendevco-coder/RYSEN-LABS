from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.models.schemas import SprintTaskStatus  # noqa: E402
from app.services.sprint_service import SprintService  # noqa: E402


ALLOWED_STATUSES = {status.value for status in SprintTaskStatus}


class SprintUpdateError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise SprintUpdateError("current_sprint.yaml must contain a YAML mapping")
    return payload


def _validate_checkpoint_totals(payload: dict[str, Any]) -> None:
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list):
        raise SprintUpdateError("current_sprint.yaml field 'tasks' must be a list")
    for task in tasks:
        if not isinstance(task, dict):
            continue
        checkpoints = task.get("checkpoints") or []
        if not checkpoints:
            continue
        checkpoint_points = sum(int(checkpoint.get("points", 0)) for checkpoint in checkpoints)
        if checkpoint_points != int(task.get("points", 0)):
            raise SprintUpdateError(
                f"Task '{task.get('id')}' checkpoint points ({checkpoint_points}) must sum to task points ({task.get('points')})",
            )


def _find_task(payload: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in payload.get("tasks", []):
        if isinstance(task, dict) and task.get("id") == task_id:
            return task
    raise SprintUpdateError(f"Task '{task_id}' was not found")


def _find_checkpoint(task: dict[str, Any], checkpoint_id: str) -> dict[str, Any]:
    for checkpoint in task.get("checkpoints", []) or []:
        if isinstance(checkpoint, dict) and checkpoint.get("id") == checkpoint_id:
            return checkpoint
    raise SprintUpdateError(f"Checkpoint '{checkpoint_id}' was not found on task '{task.get('id')}'")


def _progress_line(label: str, settings: Settings) -> str:
    sprint = SprintService(settings).load_sprint()
    return (
        f"{label}: {sprint.progress.completed_points}/{sprint.progress.total_points} points "
        f"({sprint.progress.progress_percentage}%)"
    )


def update_sprint_status(path: Path, task_id: str, status: str, checkpoint_id: str | None = None) -> str:
    if status not in ALLOWED_STATUSES:
        raise SprintUpdateError(f"Status '{status}' is invalid. Allowed statuses: {', '.join(sorted(ALLOWED_STATUSES))}")

    payload = _load_yaml(path)
    _validate_checkpoint_totals(payload)
    task = _find_task(payload, task_id)
    target = _find_checkpoint(task, checkpoint_id) if checkpoint_id else task
    before_status = target.get("status")
    target["status"] = status
    _validate_checkpoint_totals(payload)

    with path.open("w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=False)

    target_label = f"checkpoint {checkpoint_id}" if checkpoint_id else f"task {task_id}"
    return f"Updated {target_label}: {before_status} -> {status}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely update Rysen Labs sprint task/checkpoint status.")
    parser.add_argument("--task", required=True, help="Task ID to update.")
    parser.add_argument("--checkpoint", help="Optional checkpoint ID to update.")
    parser.add_argument("--status", required=True, help="New status: todo, in_progress, blocked, or done.")
    parser.add_argument("--file", default=str(ROOT / "roadmap" / "current_sprint.yaml"), help="Sprint YAML path.")
    args = parser.parse_args()

    path = Path(args.file).resolve()
    settings = Settings(current_sprint_config_path=path)
    print(_progress_line("Before", settings))
    try:
        summary = update_sprint_status(path, args.task, args.status, args.checkpoint)
    except (OSError, SprintUpdateError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(summary)
    print(_progress_line("After", settings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
