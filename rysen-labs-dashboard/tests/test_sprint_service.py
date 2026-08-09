from datetime import date
from pathlib import Path

from app.config import Settings
from app.models.schemas import ProjectSprintStatus, ScheduleStatus, SprintTask, SprintTaskStatus
from app.services.sprint_service import (
    SprintService,
    calculate_expected_progress,
    calculate_progress,
    classify_schedule_status,
)


def test_sprint_yaml_loading() -> None:
    sprint = SprintService(Settings()).load_sprint()

    assert sprint.name == "Sprint 01 - Ship Something"
    assert sprint.date_label == "Aug 10 - Aug 23, 2026"
    assert len(sprint.projects) == 4
    assert sprint.revenue_goal.description == "First $1 of recurring software revenue"


def test_task_parsing() -> None:
    task = SprintTask.model_validate(
        {
            "id": "task-1",
            "project": "rip-or-vault",
            "name": "Do the work",
            "description": "Task description",
            "points": 3,
            "status": "todo",
        },
    )

    assert task.status == SprintTaskStatus.TODO
    assert task.points == 3


def test_point_weighted_project_progress() -> None:
    tasks = [
        SprintTask(id="a", project="p", name="A", description="A", points=3, status="done"),
        SprintTask(id="b", project="p", name="B", description="B", points=7, status="todo"),
    ]

    progress = calculate_progress(tasks)

    assert progress.total_points == 10
    assert progress.completed_points == 3
    assert progress.progress_percentage == 30.0


def test_checkpoint_progress_calculation() -> None:
    task = SprintTask.model_validate(
        {
            "id": "task-with-checkpoints",
            "project": "p",
            "name": "Checkpoint task",
            "description": "Task with checkpoint progress",
            "points": 4,
            "status": "in_progress",
            "checkpoints": [
                {"id": "cp-a", "name": "A", "points": 1, "status": "done"},
                {"id": "cp-b", "name": "B", "points": 3, "status": "todo"},
            ],
        },
    )

    progress = calculate_progress([task])

    assert progress.total_points == 4
    assert progress.completed_points == 1
    assert progress.progress_percentage == 25.0


def test_mixed_checkpoint_and_non_checkpoint_tasks() -> None:
    tasks = [
        SprintTask.model_validate(
            {
                "id": "checkpoint-task",
                "project": "p",
                "name": "Checkpoint task",
                "description": "Task with checkpoints",
                "points": 4,
                "status": "in_progress",
                "checkpoints": [
                    {"id": "cp-a", "name": "A", "points": 2, "status": "done"},
                    {"id": "cp-b", "name": "B", "points": 2, "status": "todo"},
                ],
            },
        ),
        SprintTask(id="plain-task", project="p", name="Plain", description="Plain task", points=6, status="done"),
    ]

    progress = calculate_progress(tasks)

    assert progress.total_points == 10
    assert progress.completed_points == 8
    assert progress.progress_percentage == 80.0


def test_invalid_checkpoint_point_totals_are_reported(tmp_path: Path) -> None:
    projects = tmp_path / "projects.yaml"
    sprint_file = tmp_path / "current_sprint.yaml"
    projects.write_text(
        """
projects:
  - id: sample-project
    name: Sample Project
    short_name: SAMPLE
""",
        encoding="utf-8",
    )
    sprint_file.write_text(
        """
name: Invalid Checkpoints
tasks:
  - id: bad-task
    project: sample-project
    name: Bad task
    description: Bad checkpoint totals
    points: 5
    status: in_progress
    checkpoints:
      - id: cp-a
        name: A
        points: 2
        status: done
""",
        encoding="utf-8",
    )

    sprint = SprintService(Settings(projects_config_path=projects, current_sprint_config_path=sprint_file)).load_sprint()

    assert any("checkpoint points must sum to parent task points" in error for error in sprint.config_errors)


def test_overall_sprint_progress_is_point_weighted() -> None:
    sprint = SprintService(Settings()).load_sprint()

    assert sprint.progress.total_points == 36
    assert sprint.progress.completed_points == 14
    assert sprint.progress.progress_percentage == 38.9
    assert sprint.schedule.expected_progress_percentage == 0.0
    assert sprint.schedule.schedule_status == ScheduleStatus.AHEAD


def test_current_sprint_project_progress() -> None:
    sprint = SprintService(Settings()).load_sprint()
    projects = {project.id: project for project in sprint.projects}

    assert projects["rip-or-vault"].progress.total_points == 21
    assert projects["rip-or-vault"].progress.completed_points == 10
    assert projects["rip-or-vault"].progress.progress_percentage == 47.6
    assert projects["motorminder"].progress.total_points == 5
    assert projects["motorminder"].progress.completed_points == 0
    assert projects["motorminder"].progress.progress_percentage == 0.0
    assert projects["pbct"].progress.total_points == 5
    assert projects["pbct"].progress.completed_points == 0
    assert projects["pbct"].progress.progress_percentage == 0.0
    assert projects["rysen-labs-infrastructure"].progress.total_points == 5
    assert projects["rysen-labs-infrastructure"].progress.completed_points == 4
    assert projects["rysen-labs-infrastructure"].progress.progress_percentage == 80.0


def test_current_sprint_has_no_blocked_tasks() -> None:
    sprint = SprintService(Settings()).load_sprint()

    assert sprint.progress.task_counts.blocked == 0
    assert all(task.status != SprintTaskStatus.BLOCKED for task in sprint.needs_attention)


def test_blocked_task_behavior(tmp_path: Path) -> None:
    projects = tmp_path / "projects.yaml"
    sprint_file = tmp_path / "current_sprint.yaml"
    projects.write_text(
        """
projects:
  - id: sample-project
    name: Sample Project
    short_name: SAMPLE
""",
        encoding="utf-8",
    )
    sprint_file.write_text(
        """
name: Test Sprint
tasks:
  - id: blocked-1
    project: sample-project
    name: Blocked work
    description: Work that cannot proceed
    points: 5
    status: blocked
    blocker: External dependency is unavailable.
""",
        encoding="utf-8",
    )
    settings = Settings(projects_config_path=projects, current_sprint_config_path=sprint_file)
    sprint = SprintService(settings).load_sprint()
    project = sprint.projects[0]

    assert project.status == ProjectSprintStatus.BLOCKED
    assert project.progress.total_points == 5
    assert project.progress.completed_points == 0
    assert sprint.needs_attention[0].status == SprintTaskStatus.BLOCKED
    assert sprint.needs_attention[0].blocker == "External dependency is unavailable."


def test_blocked_checkpoint_behavior(tmp_path: Path) -> None:
    projects = tmp_path / "projects.yaml"
    sprint_file = tmp_path / "current_sprint.yaml"
    projects.write_text(
        """
projects:
  - id: sample-project
    name: Sample Project
    short_name: SAMPLE
""",
        encoding="utf-8",
    )
    sprint_file.write_text(
        """
name: Test Sprint
tasks:
  - id: checkpoint-task
    project: sample-project
    name: Checkpoint work
    description: Work split into checkpoints
    points: 2
    status: in_progress
    checkpoints:
      - id: cp-a
        name: A
        points: 1
        status: done
      - id: cp-b
        name: B
        points: 1
        status: blocked
        blocker: Checkpoint dependency is blocked.
""",
        encoding="utf-8",
    )

    sprint = SprintService(Settings(projects_config_path=projects, current_sprint_config_path=sprint_file)).load_sprint()

    assert sprint.projects[0].status == ProjectSprintStatus.BLOCKED
    assert sprint.projects[0].progress.completed_points == 1
    assert sprint.needs_attention[0].id == "checkpoint-task"


def test_schedule_progress_before_sprint_start() -> None:
    assert calculate_expected_progress(date(2026, 8, 10), date(2026, 8, 23), date(2026, 8, 8)) == 0.0


def test_schedule_progress_during_sprint() -> None:
    assert calculate_expected_progress(date(2026, 8, 10), date(2026, 8, 23), date(2026, 8, 16)) == 46.2


def test_schedule_progress_after_sprint() -> None:
    assert calculate_expected_progress(date(2026, 8, 10), date(2026, 8, 23), date(2026, 8, 24)) == 100.0


def test_schedule_status_classification() -> None:
    assert classify_schedule_status(36.1, 0.0, 13, 36) == ScheduleStatus.AHEAD
    assert classify_schedule_status(50.0, 52.0, 5, 10) == ScheduleStatus.ON_TRACK
    assert classify_schedule_status(40.0, 50.0, 4, 10) == ScheduleStatus.AT_RISK
    assert classify_schedule_status(20.0, 50.0, 2, 10) == ScheduleStatus.BEHIND
    assert classify_schedule_status(100.0, 80.0, 10, 10) == ScheduleStatus.COMPLETE


def test_missing_roadmap_file_behavior(tmp_path: Path) -> None:
    projects = tmp_path / "projects.yaml"
    projects.write_text("projects: []\n", encoding="utf-8")
    settings = Settings(projects_config_path=projects, current_sprint_config_path=tmp_path / "missing.yaml")

    sprint = SprintService(settings).load_sprint()

    assert sprint.name == "No active sprint"
    assert sprint.config_errors
    assert "Could not read current sprint file" in sprint.config_errors[0]


def test_invalid_roadmap_file_behavior(tmp_path: Path) -> None:
    projects = tmp_path / "projects.yaml"
    sprint_file = tmp_path / "current_sprint.yaml"
    projects.write_text("projects: not-a-list\n", encoding="utf-8")
    sprint_file.write_text("tasks: not-a-list\n", encoding="utf-8")
    settings = Settings(projects_config_path=projects, current_sprint_config_path=sprint_file)

    sprint = SprintService(settings).load_sprint()

    assert "projects.yaml field 'projects' must be a list" in sprint.config_errors
    assert "current_sprint.yaml field 'tasks' must be a list" in sprint.config_errors
