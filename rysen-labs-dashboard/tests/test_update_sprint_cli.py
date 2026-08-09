from pathlib import Path

import pytest
import yaml

from scripts.update_sprint import SprintUpdateError, update_sprint_status


def _write_sprint(path: Path) -> None:
    path.write_text(
        """
name: CLI Sprint
tasks:
  - id: task-1
    project: sample-project
    name: Task one
    description: Task-level update
    points: 2
    status: todo
  - id: task-2
    project: sample-project
    name: Task two
    description: Checkpoint update
    points: 2
    status: in_progress
    checkpoints:
      - id: cp-a
        name: A
        points: 1
        status: todo
      - id: cp-b
        name: B
        points: 1
        status: todo
""",
        encoding="utf-8",
    )


def test_cli_task_update_validation(tmp_path: Path) -> None:
    sprint = tmp_path / "current_sprint.yaml"
    _write_sprint(sprint)

    summary = update_sprint_status(sprint, "task-1", "done")
    payload = yaml.safe_load(sprint.read_text(encoding="utf-8"))

    assert summary == "Updated task task-1: todo -> done"
    assert payload["tasks"][0]["status"] == "done"
    assert payload["tasks"][1]["status"] == "in_progress"


def test_cli_checkpoint_update_validation(tmp_path: Path) -> None:
    sprint = tmp_path / "current_sprint.yaml"
    _write_sprint(sprint)

    summary = update_sprint_status(sprint, "task-2", "done", checkpoint_id="cp-a")
    payload = yaml.safe_load(sprint.read_text(encoding="utf-8"))

    assert summary == "Updated checkpoint cp-a: todo -> done"
    assert payload["tasks"][1]["checkpoints"][0]["status"] == "done"
    assert payload["tasks"][1]["checkpoints"][1]["status"] == "todo"


def test_cli_rejects_invalid_status(tmp_path: Path) -> None:
    sprint = tmp_path / "current_sprint.yaml"
    _write_sprint(sprint)

    with pytest.raises(SprintUpdateError, match="Status 'started' is invalid"):
        update_sprint_status(sprint, "task-1", "started")


def test_cli_rejects_missing_task(tmp_path: Path) -> None:
    sprint = tmp_path / "current_sprint.yaml"
    _write_sprint(sprint)

    with pytest.raises(SprintUpdateError, match="Task 'missing' was not found"):
        update_sprint_status(sprint, "missing", "done")


def test_cli_rejects_missing_checkpoint(tmp_path: Path) -> None:
    sprint = tmp_path / "current_sprint.yaml"
    _write_sprint(sprint)

    with pytest.raises(SprintUpdateError, match="Checkpoint 'missing' was not found"):
        update_sprint_status(sprint, "task-2", "done", checkpoint_id="missing")


def test_cli_refuses_invalid_checkpoint_totals(tmp_path: Path) -> None:
    sprint = tmp_path / "current_sprint.yaml"
    sprint.write_text(
        """
tasks:
  - id: task-1
    project: sample-project
    name: Bad task
    description: Bad totals
    points: 3
    status: in_progress
    checkpoints:
      - id: cp-a
        name: A
        points: 1
        status: todo
""",
        encoding="utf-8",
    )

    with pytest.raises(SprintUpdateError, match="checkpoint points"):
        update_sprint_status(sprint, "task-1", "done", checkpoint_id="cp-a")
