from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from app.config import Settings
from app.services.sprint_service import SprintService
from tests.test_sprint_sync_service import _settings_env, _write_fixture


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


def _write_git_repo(path: Path) -> str:
    path.mkdir(parents=True)
    _git(["init"], path)
    _git(["config", "user.email", "checkpoint@example.test"], path)
    _git(["config", "user.name", "Checkpoint Test"], path)
    (path / "README.md").write_text("# checkpoint fixture\n", encoding="utf-8")
    _git(["add", "README.md"], path)
    _git(["commit", "-m", "Fixture checkpoint"], path)
    remote = path.parent / f"{path.name}.git"
    _git(["init", "--bare", str(remote)], path.parent)
    _git(["remote", "add", "origin", str(remote)], path)
    branch = _git(["branch", "--show-current"], path)
    _git(["push", "-u", "origin", branch], path)
    return _git(["rev-parse", "HEAD"], path)


def _run_checkpoint(
    settings: Settings,
    repo: Path,
    *extra: str,
    status: str = "done",
    validation_command: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = _settings_env(settings)
    env["PYTHONPATH"] = str(ROOT)
    command = [
        POWERSHELL,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ROOT / "scripts" / "checkpoint.ps1"),
        "-Project",
        "rip-or-vault",
        "-Task",
        "rov-002",
        "-Checkpoint",
        "rov-002-a",
        "-Status",
        status,
        "-RepositoryPath",
        str(repo),
        "-DashboardRoot",
        str(ROOT),
        "-PythonExe",
        sys.executable,
        *extra,
    ]
    if validation_command is not None:
        command.extend(["-ValidationCommand", validation_command])
    return subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)


def test_checkpoint_ps1_valid_apply_updates_data_and_captures_git_metadata(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    repo = tmp_path / "project"
    commit = _write_git_repo(repo)

    result = _run_checkpoint(settings, repo, "-Apply", validation_command="Write-Output validation-ok")

    assert result.returncode == 0, result.stderr
    sprint = SprintService(settings).load_sprint()
    assert sprint.progress.completed_points == 1
    processed = list((settings.sprint_updates_dir / "processed").glob("*.json"))
    assert len(processed) == 1
    payload = json.loads(processed[0].read_text(encoding="utf-8-sig"))
    evidence = payload["sprint_update"]["evidence"]
    assert evidence["commit"] == commit
    assert evidence["commit_message"] == "Fixture checkpoint"
    assert evidence["repository"] == "project"


def test_checkpoint_ps1_duplicate_execution_is_idempotent(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    repo = tmp_path / "project"
    _write_git_repo(repo)

    first = _run_checkpoint(settings, repo, "-Apply", validation_command="Write-Output validation-ok")
    second = _run_checkpoint(settings, repo, "-Apply", validation_command="Write-Output validation-ok")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert "already_processed: True" in second.stdout
    assert SprintService(settings).load_sprint().progress.completed_points == 1


def test_checkpoint_ps1_invalid_project_fails_safely(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    repo = tmp_path / "project"
    _write_git_repo(repo)

    result = subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "checkpoint.ps1"),
            "-Project",
            "unknown-project",
            "-Task",
            "rov-002",
            "-Checkpoint",
            "rov-002-a",
            "-Status",
            "done",
            "-RepositoryPath",
            str(repo),
            "-DashboardRoot",
            str(ROOT),
            "-PythonExe",
            sys.executable,
            "-ValidationCommand",
            "Write-Output validation-ok",
            "-Apply",
        ],
        cwd=ROOT,
        env={**os.environ.copy(), **_settings_env(settings), "PYTHONPATH": str(ROOT)},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert SprintService(settings).load_sprint().progress.completed_points == 0
    assert list((settings.sprint_updates_dir / "rejected").glob("*.json"))


def test_checkpoint_ps1_failed_validation_does_not_write_update(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    repo = tmp_path / "project"
    _write_git_repo(repo)

    result = _run_checkpoint(settings, repo, validation_command="exit 7")

    assert result.returncode == 1
    assert SprintService(settings).load_sprint().progress.completed_points == 0
    assert not list((settings.sprint_updates_dir / "pending").glob("*.json"))
    assert not list((settings.sprint_updates_dir / "processed").glob("*.json"))


def test_checkpoint_ps1_missing_validation_blocks_automatic_done(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    repo = tmp_path / "project"
    _write_git_repo(repo)

    result = _run_checkpoint(settings, repo, "-Apply")

    assert result.returncode == 1
    assert "requires a configured or supplied validation command" in result.stderr
    assert SprintService(settings).load_sprint().progress.completed_points == 0
    assert not list((settings.sprint_updates_dir / "pending").glob("*.json"))


def test_checkpoint_ps1_dirty_source_repo_blocks_automatic_completion(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    repo = tmp_path / "project"
    _write_git_repo(repo)
    (repo / "README.md").write_text("# dirty checkpoint fixture\n", encoding="utf-8")

    result = _run_checkpoint(settings, repo, "-Apply", validation_command="Write-Output validation-ok")

    assert result.returncode == 1
    assert "Working tree is dirty" in result.stderr
    assert SprintService(settings).load_sprint().progress.completed_points == 0


def test_checkpoint_ps1_unsynchronized_source_repo_blocks_automatic_completion(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    repo = tmp_path / "project"
    _write_git_repo(repo)
    (repo / "CHANGELOG.md").write_text("# local only\n", encoding="utf-8")
    _git(["add", "CHANGELOG.md"], repo)
    _git(["commit", "-m", "Unpushed checkpoint"], repo)

    result = _run_checkpoint(settings, repo, "-Apply", validation_command="Write-Output validation-ok")

    assert result.returncode == 1
    assert "Project branch" in result.stderr
    assert SprintService(settings).load_sprint().progress.completed_points == 0


def test_checkpoint_ps1_reopened_task_recalculates_progress(tmp_path: Path) -> None:
    settings = _write_fixture(tmp_path)
    repo = tmp_path / "project"
    _write_git_repo(repo)
    done = _run_checkpoint(settings, repo, "-Apply", validation_command="Write-Output validation-ok")
    assert done.returncode == 0, done.stderr

    reopen = _run_checkpoint(
        settings,
        repo,
        "-UpdateId",
        "reopen-rov-002-a",
        "-SkipValidation",
        "-Apply",
        status="todo",
    )
    payload = yaml.safe_load(settings.current_sprint_config_path.read_text(encoding="utf-8"))
    task = next(task for task in payload["tasks"] if task["id"] == "rov-002")

    assert reopen.returncode == 0, reopen.stderr
    assert task["checkpoints"][0]["status"] == "todo"
    assert SprintService(settings).load_sprint().progress.completed_points == 0


def test_zima_sync_script_uses_safe_fast_forward_only() -> None:
    script = (ROOT / "scripts" / "zima_sync.sh").read_text(encoding="utf-8")

    assert "/home/charles/projects/RYSEN-LABS" in script
    assert "/opt/rysen-labs-dashboard" not in script
    assert "status --porcelain" in script
    assert "merge --ff-only" in script
    assert "refusing sync: working tree is dirty" in script
    assert "cannot fast-forward" in script
    assert "reset --hard" not in script
    assert "docker" not in script.lower()


def test_zima_sync_systemd_service_uses_confirmed_host_paths() -> None:
    service = (ROOT / "deploy" / "systemd" / "rysen-labs-dashboard-sync.service").read_text(encoding="utf-8")

    assert "WorkingDirectory=/home/charles/projects/RYSEN-LABS" in service
    assert "Environment=RYSEN_DASHBOARD_DIR=/home/charles/projects/RYSEN-LABS" in service
    assert "ExecStart=/home/charles/projects/RYSEN-LABS/rysen-labs-dashboard/scripts/zima_sync.sh" in service
    assert "/opt/rysen-labs-dashboard" not in service


def test_checkpoint_ps1_commit_state_mode_has_dashboard_guards() -> None:
    script = (ROOT / "scripts" / "checkpoint.ps1").read_text(encoding="utf-8")

    assert "Assert-DashboardCleanBeforeMutation" in script
    assert "Assert-DashboardChangesExpected" in script
    assert "Invoke-DashboardValidation" in script
    assert "git commit -m" in script
    assert "git push" in script
