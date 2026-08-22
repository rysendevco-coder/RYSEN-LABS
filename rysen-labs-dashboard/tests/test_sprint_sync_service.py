from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

from app.config import Settings
from app.models.schemas import SprintTaskStatus
from app.services.sprint_service import SprintService
from app.services.sprint_snapshot_service import SprintSnapshotService
from app.services.sprint_sync_service import SprintUpdateInboxService


def _write_fixture(tmp_path: Path) -> Settings:
    roadmap = tmp_path / "roadmap"
    updates = roadmap / "updates"
    for folder in ("pending", "processed", "rejected"):
        (updates / folder).mkdir(parents=True, exist_ok=True)
    (roadmap / "history").mkdir(parents=True, exist_ok=True)
    projects = roadmap / "projects.yaml"
    sprint = roadmap / "current_sprint.yaml"
    projects.write_text(
        """
projects:
  - id: rip-or-vault
    name: Rip or Vault
    short_name: ROV
  - id: motorminder
    name: MotorMinder
    short_name: MM
  - id: lunch-roulette
    name: Lunch Roulette
    short_name: LUNCH ROULETTE
""",
        encoding="utf-8",
    )
    sprint.write_text(
        """
name: Test Sprint
start_date: 2026-08-10
end_date: 2026-08-23
date_label: Aug 10 - Aug 23, 2026
primary_objective: Test sprint objective
tasks:
  - id: rov-002
    project: rip-or-vault
    name: Evaluation flow
    description: Validate flow
    points: 2
    status: in_progress
    checkpoints:
      - id: rov-002-a
        name: Result state
        points: 1
        status: todo
      - id: rov-002-b
        name: Error state
        points: 1
        status: todo
  - id: mm-001
    project: motorminder
    name: Starting point
    description: Define first slice
    points: 3
    status: todo
""",
        encoding="utf-8",
    )
    return Settings(
        projects_config_path=projects,
        current_sprint_config_path=sprint,
        sprint_updates_dir=updates,
        sprint_history_dir=roadmap / "history",
    )


def _write_update(path: Path, **overrides: object) -> Path:
    payload = {
        "update_id": "rov-result-state-001",
        "sprint_update": {
            "project": "rip-or-vault",
            "task": "rov-002",
            "checkpoint": "rov-002-a",
            "result": "passed",
            "evidence": {"tests": "3 passed"},
            "recommendation": {"status": "done"},
        },
    }
    for key, value in overrides.items():
        if key in payload["sprint_update"] or key == "activity_only":
            payload["sprint_update"][key] = value
        else:
            payload[key] = value
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_valid_update_parsing(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(settings.sprint_updates_dir / "pending" / "valid.yaml")

    update_id, update, status = SprintUpdateInboxService(settings).validate_update(path)

    assert update_id == "rov-result-state-001"
    assert update.project == "rip-or-vault"
    assert update.task == "rov-002"
    assert update.checkpoint == "rov-002-a"
    assert status == SprintTaskStatus.DONE


def test_malformed_update_rejection(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = settings.sprint_updates_dir / "pending" / "bad.yaml"
    path.write_text("sprint_update: []\n", encoding="utf-8")

    record = SprintUpdateInboxService(settings).process_file(path, apply=True)

    assert record.validation_error
    assert not path.exists()
    assert list((settings.sprint_updates_dir / "rejected").glob("*.yaml"))


def test_unknown_project_task_checkpoint_and_invalid_status(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    inbox = SprintUpdateInboxService(settings)
    cases = [
        {"project": "unknown-project"},
        {"task": "unknown-task"},
        {"checkpoint": "unknown-checkpoint"},
        {"recommendation": {"status": "invalid"}},
    ]

    for index, overrides in enumerate(cases):
        path = _write_update(settings.sprint_updates_dir / "pending" / f"bad-{index}.yaml", **overrides)
        record = inbox.process_file(path, apply=False)
        assert record.validation_error


def test_completion_update_requires_objective_evidence(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(
        settings.sprint_updates_dir / "pending" / "weak-evidence.yaml",
        evidence=None,
    )

    record = SprintUpdateInboxService(settings).process_file(path, apply=False)

    assert record.validation_error == "completion updates require objective validation evidence"


def test_no_validation_command_does_not_qualify_as_done_evidence(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(
        settings.sprint_updates_dir / "pending" / "no-validation.yaml",
        evidence={"validation": "No validation command configured.", "commit": "abc1234"},
    )

    record = SprintUpdateInboxService(settings).process_file(path, apply=False)

    assert record.validation_error == "completion updates require a real validation command or test evidence"


def test_registered_project_without_active_sprint_task_is_rejected_by_task(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(
        settings.sprint_updates_dir / "pending" / "lunch-roulette.yaml",
        update_id="lunch-roulette-checkpoint-8",
        project="lunch-roulette",
        task="lr-009",
        checkpoint="lr-009-a",
    )

    record = SprintUpdateInboxService(settings).process_file(path, apply=False)

    assert record.validation_error == "Unknown task 'lr-009'"


def test_activity_only_update_for_out_of_sprint_project_does_not_change_sprint_math(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(
        settings.sprint_updates_dir / "pending" / "lunch-roulette-activity.yaml",
        update_id="lunch-roulette-checkpoint-8",
        project="lunch-roulette",
        task="lr-008",
        checkpoint="lr-008-a",
        activity_only=True,
        evidence={"tests": "71 passed", "commit": "4b882661e9f9d652c7b9852865a433011108e59a"},
    )

    record = SprintUpdateInboxService(settings).process_file(path, apply=True)
    sprint = SprintService(settings).load_sprint()
    projects = {project.id: project for project in sprint.projects}

    assert not record.applied
    assert record.activity_only
    assert sprint.progress.completed_points == 0
    assert projects["lunch-roulette"].update_count == 1
    assert projects["lunch-roulette"].last_processed_checkpoint == "lr-008-a"
    assert projects["lunch-roulette"].latest_source_commit_sha == "4b882661e9f9d652c7b9852865a433011108e59a"


def test_dry_run_does_not_mutate_state_or_move_file(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(settings.sprint_updates_dir / "pending" / "valid.yaml")
    before = settings.current_sprint_config_path.read_text(encoding="utf-8")

    record = SprintUpdateInboxService(settings).process_file(path, apply=False)

    assert not record.applied
    assert path.exists()
    assert settings.current_sprint_config_path.read_text(encoding="utf-8") == before
    assert SprintService(settings).load_sprint().progress.completed_points == 0


def test_apply_updates_only_requested_status_and_preserves_points(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(settings.sprint_updates_dir / "pending" / "valid.yaml")

    record = SprintUpdateInboxService(settings).process_file(path, apply=True)
    sprint_payload = yaml.safe_load(settings.current_sprint_config_path.read_text(encoding="utf-8"))
    task = next(task for task in sprint_payload["tasks"] if task["id"] == "rov-002")

    assert record.applied
    assert not path.exists()
    assert task["points"] == 2
    assert task["checkpoints"][0]["status"] == "done"
    assert task["checkpoints"][1]["status"] == "todo"
    assert SprintService(settings).load_sprint().progress.completed_points == 1
    assert list((settings.sprint_updates_dir / "processed").glob("*.yaml"))


def test_duplicate_update_is_idempotent(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    inbox = SprintUpdateInboxService(settings)
    first = _write_update(settings.sprint_updates_dir / "pending" / "first.yaml")
    assert inbox.process_file(first, apply=True).applied
    second = _write_update(settings.sprint_updates_dir / "pending" / "second.yaml")

    record = inbox.process_file(second, apply=True)

    assert record.already_processed
    assert not record.applied
    assert SprintService(settings).load_sprint().progress.completed_points == 1


def test_processed_recent_updates_and_project_freshness(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(settings.sprint_updates_dir / "pending" / "valid.yaml")
    SprintUpdateInboxService(settings).process_file(path, apply=True)

    sprint = SprintService(settings).load_sprint()

    freshness = {project.project: project for project in sprint.sync_projects}

    assert sprint.recent_updates[0].project == "rip-or-vault"
    assert freshness["rip-or-vault"].last_processed_checkpoint == "rov-002-a"
    assert freshness["rip-or-vault"].update_count == 1


def test_snapshot_creation_and_duplicate_daily_snapshot(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    service = SprintSnapshotService(settings)

    first = service.write_snapshot()
    second = service.write_snapshot()

    assert first == second
    payload = yaml.safe_load(first.read_text(encoding="utf-8"))
    assert payload["sprint"]["total_points"] == 5
    projects = {project["id"]: project for project in payload["projects"]}
    assert projects["rip-or-vault"]["total_points"] == 2


def test_process_sprint_updates_cli_dry_run(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(settings.sprint_updates_dir / "pending" / "valid.yaml")
    env = _settings_env(settings)

    result = subprocess.run(
        [sys.executable, "scripts/process_sprint_updates.py", "--dry-run", "--all"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "applied: False" in result.stdout
    assert path.exists()
    assert SprintService(settings).load_sprint().progress.completed_points == 0


def test_process_sprint_updates_cli_apply_file(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    path = _write_update(settings.sprint_updates_dir / "pending" / "valid.yaml")
    env = _settings_env(settings)

    result = subprocess.run(
        [sys.executable, "scripts/process_sprint_updates.py", "--apply", "--file", str(path)],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "applied: True" in result.stdout
    assert not path.exists()
    assert SprintService(settings).load_sprint().progress.completed_points == 1


def _settings_env(settings: Settings) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PROJECTS_CONFIG_PATH": str(settings.projects_config_path),
            "CURRENT_SPRINT_CONFIG_PATH": str(settings.current_sprint_config_path),
            "SPRINT_UPDATES_DIR": str(settings.sprint_updates_dir),
            "SPRINT_HISTORY_DIR": str(settings.sprint_history_dir),
        },
    )
    return env
