from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError
import yaml

from app.config import Settings
from app.models.schemas import (
    ProjectConfig,
    ProjectSprintStatus,
    SprintBrief,
    SprintBriefProject,
    ScheduleStatus,
    SprintCheckpoint,
    ProjectSprintSummary,
    SprintProgress,
    SprintRevenueGoal,
    SprintSchedule,
    SprintSummary,
    SprintTask,
    SprintTaskStatus,
    TaskCounts,
)
from app.services.sprint_sync_service import SprintUpdateInboxService


logger = logging.getLogger(__name__)


def _load_yaml(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    except OSError as exc:
        return {}, [f"Could not read {label} file at {path}: {exc}"]
    if not isinstance(payload, dict):
        return {}, [f"{label} file must contain a YAML mapping"]
    return payload, []


def _task_counts(tasks: list[SprintTask]) -> TaskCounts:
    return TaskCounts(
        todo=sum(1 for task in tasks if task.status == SprintTaskStatus.TODO),
        in_progress=sum(1 for task in tasks if task.status == SprintTaskStatus.IN_PROGRESS),
        blocked=sum(1 for task in tasks if task.status == SprintTaskStatus.BLOCKED),
        done=sum(1 for task in tasks if task.status == SprintTaskStatus.DONE),
    )


def _completed_points_for_task(task: SprintTask) -> int:
    if task.checkpoints:
        return sum(checkpoint.points for checkpoint in task.checkpoints if checkpoint.status == SprintTaskStatus.DONE)
    return task.points if task.status == SprintTaskStatus.DONE else 0


def _task_is_blocked(task: SprintTask) -> bool:
    return task.status == SprintTaskStatus.BLOCKED or any(
        checkpoint.status == SprintTaskStatus.BLOCKED for checkpoint in task.checkpoints
    )


def calculate_progress(tasks: list[SprintTask]) -> SprintProgress:
    total_points = sum(task.points for task in tasks)
    completed_points = sum(_completed_points_for_task(task) for task in tasks)
    percentage = round((completed_points / total_points * 100), 1) if total_points else 0.0
    return SprintProgress(
        total_points=total_points,
        completed_points=completed_points,
        progress_percentage=percentage,
        task_counts=_task_counts(tasks),
    )


def _project_status(tasks: list[SprintTask]) -> ProjectSprintStatus:
    if not tasks:
        return ProjectSprintStatus.ON_TRACK
    if all(_completed_points_for_task(task) == task.points for task in tasks):
        return ProjectSprintStatus.COMPLETE
    if any(_task_is_blocked(task) for task in tasks):
        return ProjectSprintStatus.BLOCKED
    if any(task.status == SprintTaskStatus.IN_PROGRESS for task in tasks):
        return ProjectSprintStatus.IN_PROGRESS
    return ProjectSprintStatus.ON_TRACK


def _current_focus(tasks: list[SprintTask]) -> str:
    for status in (SprintTaskStatus.IN_PROGRESS, SprintTaskStatus.BLOCKED, SprintTaskStatus.TODO):
        task = next((item for item in tasks if item.status == status), None)
        if task:
            return task.name
    return "No active sprint work"


def _parse_sprint_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def calculate_expected_progress(start_date: date | None, end_date: date | None, as_of: date) -> float:
    if start_date is None or end_date is None:
        return 0.0
    if as_of < start_date:
        return 0.0
    if as_of >= end_date:
        return 100.0
    total_days = max((end_date - start_date).days, 1)
    elapsed_days = max((as_of - start_date).days, 0)
    return round((elapsed_days / total_days) * 100, 1)


def classify_schedule_status(actual: float, expected: float, completed_points: int, total_points: int) -> ScheduleStatus:
    if total_points > 0 and completed_points >= total_points:
        return ScheduleStatus.COMPLETE
    variance = round(actual - expected, 1)
    if variance >= 10:
        return ScheduleStatus.AHEAD
    if variance >= -5:
        return ScheduleStatus.ON_TRACK
    if variance >= -15:
        return ScheduleStatus.AT_RISK
    return ScheduleStatus.BEHIND


def calculate_schedule(progress: SprintProgress, start_date: date | None, end_date: date | None, as_of: date) -> SprintSchedule:
    expected = calculate_expected_progress(start_date, end_date, as_of)
    variance = round(progress.progress_percentage - expected, 1)
    return SprintSchedule(
        expected_progress_percentage=expected,
        schedule_variance=variance,
        schedule_status=classify_schedule_status(
            progress.progress_percentage,
            expected,
            progress.completed_points,
            progress.total_points,
        ),
    )


class SprintService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def load_projects(self) -> tuple[list[ProjectConfig], list[str]]:
        payload, errors = _load_yaml(self.settings.projects_config_path, "projects")
        if errors:
            logger.error("projects_config_read_failed", extra={"event": "projects_config_read_failed"})
            return [], errors
        raw_projects = payload.get("projects", [])
        if not isinstance(raw_projects, list):
            return [], ["projects.yaml field 'projects' must be a list"]

        projects: list[ProjectConfig] = []
        for index, raw in enumerate(raw_projects):
            try:
                projects.append(ProjectConfig.model_validate(raw))
            except ValidationError as exc:
                errors.append(f"Project entry {index + 1} is invalid: {exc.errors()[0]['msg']}")
        projects.sort(key=lambda project: (project.display_order, project.name.lower()))
        return projects, errors

    def load_sprint(self, as_of: date | None = None) -> SprintSummary:
        projects, errors = self.load_projects()
        payload, sprint_errors = _load_yaml(self.settings.current_sprint_config_path, "current sprint")
        errors.extend(sprint_errors)

        raw_tasks = payload.get("tasks", [])
        tasks: list[SprintTask] = []
        if not isinstance(raw_tasks, list):
            errors.append("current_sprint.yaml field 'tasks' must be a list")
        else:
            for index, raw in enumerate(raw_tasks):
                try:
                    tasks.append(SprintTask.model_validate(raw))
                except ValidationError as exc:
                    errors.append(f"Sprint task entry {index + 1} is invalid: {exc.errors()[0]['msg']}")

        known_projects = {project.id for project in projects}
        for task in tasks:
            if task.project not in known_projects:
                errors.append(f"Sprint task '{task.id}' references unknown project '{task.project}'")

        project_summaries = [
            self._project_summary(project, [task for task in tasks if task.project == project.id])
            for project in projects
        ]
        needs_attention = [
            task for task in tasks if _task_is_blocked(task)
        ] or [
            task for task in tasks if task.status in {SprintTaskStatus.IN_PROGRESS, SprintTaskStatus.TODO}
        ][:3]

        revenue_goal_raw = payload.get("revenue_goal", {}) if isinstance(payload.get("revenue_goal", {}), dict) else {}
        progress = calculate_progress(tasks)
        start = _parse_sprint_date(payload.get("start_date"))
        end = _parse_sprint_date(payload.get("end_date"))
        sync = SprintUpdateInboxService(self.settings)
        project_ids = [project.id for project in projects]
        return SprintSummary(
            name=str(payload.get("name", "No active sprint")),
            start_date=str(payload.get("start_date", "")),
            end_date=str(payload.get("end_date", "")),
            date_label=str(payload.get("date_label", "")),
            primary_objective=str(payload.get("primary_objective", "")),
            revenue_goal=SprintRevenueGoal(
                name=str(revenue_goal_raw.get("name", "Rysen Labs Goal #1")),
                description=str(
                    revenue_goal_raw.get("description", "First $1 of recurring software revenue"),
                ),
            ),
            projects=project_summaries,
            needs_attention=needs_attention,
            progress=progress,
            schedule=calculate_schedule(progress, start, end, as_of or date.today()),
            recent_updates=sync.recent_processed_updates(),
            sync_projects=sync.project_freshness(project_ids),
            config_errors=errors,
        )

    def _project_summary(self, project: ProjectConfig, tasks: list[SprintTask]) -> ProjectSprintSummary:
        return ProjectSprintSummary(
            id=project.id,
            name=project.name,
            short_name=project.short_name,
            description=project.description,
            status=_project_status(tasks),
            current_focus=_current_focus(tasks),
            blockers=[task for task in tasks if _task_is_blocked(task)],
            tasks=tasks,
            progress=calculate_progress(tasks),
            display_order=project.display_order,
        )

    def load_brief(self, as_of: date | None = None) -> SprintBrief:
        today = as_of or date.today()
        sprint = self.load_sprint(as_of=today)
        end = _parse_sprint_date(sprint.end_date)
        days_remaining = max((end - today).days, 0) if end else None
        sync_by_project = {summary.project: summary for summary in sprint.sync_projects}

        blockers: list[SprintTask] = []
        next_incomplete: list[dict[str, str]] = []
        for project in sprint.projects:
            blockers.extend(project.blockers)
            for task in project.tasks:
                if task.checkpoints:
                    checkpoint = next((item for item in task.checkpoints if item.status != SprintTaskStatus.DONE), None)
                    if checkpoint:
                        next_incomplete.append(
                            {
                                "project": project.id,
                                "task": task.id,
                                "checkpoint": checkpoint.id,
                                "name": checkpoint.name,
                                "status": checkpoint.status.value,
                            },
                        )
                        break
                elif task.status != SprintTaskStatus.DONE:
                    next_incomplete.append(
                        {
                            "project": project.id,
                            "task": task.id,
                            "checkpoint": "",
                            "name": task.name,
                            "status": task.status.value,
                        },
                    )
                    break

        return SprintBrief(
            sprint_name=sprint.name,
            days_remaining=days_remaining,
            actual_progress=sprint.progress.progress_percentage,
            expected_progress=sprint.schedule.expected_progress_percentage,
            variance=sprint.schedule.schedule_variance,
            schedule_status=sprint.schedule.schedule_status,
            per_project_progress=[
                SprintBriefProject(
                    id=project.id,
                    name=project.name,
                    completed_points=project.progress.completed_points,
                    total_points=project.progress.total_points,
                    progress_percentage=project.progress.progress_percentage,
                    status=project.status,
                    last_update_time=sync_by_project.get(project.id).last_update_time
                    if sync_by_project.get(project.id)
                    else None,
                    last_processed_checkpoint=sync_by_project.get(project.id).last_processed_checkpoint
                    if sync_by_project.get(project.id)
                    else None,
                    update_count=sync_by_project.get(project.id).update_count
                    if sync_by_project.get(project.id)
                    else 0,
                )
                for project in sprint.projects
            ],
            recent_processed_updates=sprint.recent_updates,
            blockers=blockers,
            next_incomplete_checkpoints=next_incomplete[:6],
        )
