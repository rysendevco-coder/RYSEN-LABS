from pathlib import Path

from app.config import Settings
from app.models.schemas import ProjectSprintStatus, SprintTask, SprintTaskStatus
from app.services.sprint_service import SprintService, calculate_progress


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


def test_overall_sprint_progress_is_point_weighted() -> None:
    sprint = SprintService(Settings()).load_sprint()

    assert sprint.progress.total_points == 36
    assert sprint.progress.completed_points == 9
    assert sprint.progress.progress_percentage == 25.0


def test_current_sprint_project_progress() -> None:
    sprint = SprintService(Settings()).load_sprint()
    projects = {project.id: project for project in sprint.projects}

    assert projects["rip-or-vault"].progress.total_points == 21
    assert projects["rip-or-vault"].progress.completed_points == 5
    assert projects["rip-or-vault"].progress.progress_percentage == 23.8
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
