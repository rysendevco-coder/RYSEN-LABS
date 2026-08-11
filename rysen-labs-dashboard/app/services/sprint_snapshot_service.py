from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.config import Settings
from app.services.sprint_service import SprintService


class SprintSnapshotService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def snapshot_for_day(self, snapshot_date: date | None = None) -> tuple[Path, dict[str, Any]]:
        day = snapshot_date or date.today()
        sprint = SprintService(self.settings).load_sprint(as_of=day)
        payload: dict[str, Any] = {
            "date": day.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sprint": {
                "name": sprint.name,
                "completed_points": sprint.progress.completed_points,
                "total_points": sprint.progress.total_points,
                "actual_percentage": sprint.progress.progress_percentage,
                "expected_percentage": sprint.schedule.expected_progress_percentage,
                "variance": sprint.schedule.schedule_variance,
                "schedule_status": sprint.schedule.schedule_status.value,
            },
            "projects": [
                {
                    "id": project.id,
                    "name": project.name,
                    "completed_points": project.progress.completed_points,
                    "total_points": project.progress.total_points,
                    "progress_percentage": project.progress.progress_percentage,
                    "status": project.status.value,
                }
                for project in sprint.projects
            ],
        }
        path = self.settings.sprint_history_dir / f"{day.isoformat()}.yaml"
        return path, payload

    def write_snapshot(self, snapshot_date: date | None = None) -> Path:
        path, payload = self.snapshot_for_day(snapshot_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=False)
        return path
