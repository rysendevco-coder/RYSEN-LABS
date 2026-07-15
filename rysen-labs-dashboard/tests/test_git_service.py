from __future__ import annotations

from pathlib import Path
import subprocess
from subprocess import CompletedProcess

from app.config import Settings
from app.models.schemas import RepositoryConfig, RepositoryStatusClass
from app.services.git_service import GitRepositoryService, clear_git_snapshot_cache, sanitize_remote_url
from app.services.repository_registry import RepositoryRegistry


def test_repository_registry_loads_valid_entries(tmp_path: Path) -> None:
    config = tmp_path / "repositories.yml"
    repo = tmp_path / "repo"
    config.write_text(
        f"""
repositories:
  - id: demo-repo
    name: Demo Repo
    description: Test repository
    path: {repo.as_posix()}
    category: Tests
    expected_remote: origin
    default_branch: main
    enabled: true
    display_order: 2
""",
        encoding="utf-8",
    )

    repositories, errors = RepositoryRegistry(config).load()

    assert errors == []
    assert repositories[0].id == "demo-repo"
    assert repositories[0].path == repo.resolve()


def test_repository_registry_reports_invalid_entries(tmp_path: Path) -> None:
    config = tmp_path / "repositories.yml"
    config.write_text(
        """
repositories:
  - id: bad id
    name: Bad
    path: /tmp/bad
""",
        encoding="utf-8",
    )

    repositories, errors = RepositoryRegistry(config).load()

    assert repositories == []
    assert "Repository entry 1 is invalid" in errors[0]


def test_sanitize_remote_url_removes_credentials() -> None:
    assert sanitize_remote_url("https://user:token@example.com/org/repo.git") == "https://example.com/org/repo.git"
    assert sanitize_remote_url("git@example.com:org/repo.git") == "example.com:org/repo.git"


def test_git_integration_disabled_does_not_read_registry(tmp_path: Path) -> None:
    missing_config = tmp_path / "missing.yml"
    settings = Settings(enable_git_integration=False, repositories_config_path=missing_config)

    repositories, errors = GitRepositoryService(settings).snapshot()

    assert repositories == []
    assert errors == []


def test_repository_registry_missing_file_reports_error(tmp_path: Path) -> None:
    repositories, errors = RepositoryRegistry(tmp_path / "missing.yml").load()

    assert repositories == []
    assert "Could not read repositories configuration" in errors[0]


def test_git_service_reports_repository_status(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://user:token@example.com/org/repo.git"],
        cwd=repo,
        check=True,
    )

    config = tmp_path / "repositories.yml"
    config.write_text(
        f"""
repositories:
  - id: demo-repo
    name: Demo Repo
    path: {repo.as_posix()}
    expected_remote: origin
    default_branch: main
""",
        encoding="utf-8",
    )
    settings = Settings(
        enable_git_integration=True,
        repositories_config_path=config,
        git_command_timeout_seconds=5,
    )

    repositories, errors = GitRepositoryService(settings).snapshot()

    assert errors == []
    status = repositories[0]
    assert status.valid_git_repository is True
    assert status.current_commit_sha is not None
    assert status.short_commit_sha == status.current_commit_sha[:7]
    assert status.latest_commit_message == "Initial commit"
    assert status.remote_url == "https://example.com/org/repo.git"
    assert status.working_tree_clean is True
    assert status.status_class == RepositoryStatusClass.HEALTHY


def test_git_service_reports_unavailable_when_git_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    settings = Settings(enable_git_integration=True, git_scan_cache_seconds=0)
    service = GitRepositoryService(settings)
    service.git_executable = None

    status = service.repository_status(
        RepositoryConfig(id="demo", name="Demo", path=repo),
    )

    assert status.status_class == RepositoryStatusClass.UNAVAILABLE
    assert status.warning == "Git executable is not available"


def test_git_command_timeout_is_reported(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(git_command_timeout_seconds=0.001, git_scan_cache_seconds=0)
    service = GitRepositoryService(settings)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=0.001)

    monkeypatch.setattr(subprocess, "run", timeout)

    result = service._git(tmp_path, ["--version"])

    assert result.ok is False
    assert result.timed_out is True
    assert result.stderr == "Git command timed out"


def test_git_output_is_bounded(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(git_scan_cache_seconds=0)
    service = GitRepositoryService(settings)

    def huge_output(*args, **kwargs):
        return CompletedProcess(args=["git"], returncode=0, stdout="x" * 25_000, stderr="y" * 25_000)

    monkeypatch.setattr(subprocess, "run", huge_output)

    result = service._git(tmp_path, ["status"])

    assert len(result.stdout) <= 20_000
    assert len(result.stderr) <= 20_000


def test_git_snapshot_failure_does_not_escape(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "repositories.yml"
    config.write_text("repositories: []\n", encoding="utf-8")
    settings = Settings(
        enable_git_integration=True,
        repositories_config_path=config,
        git_scan_cache_seconds=0,
    )
    service = GitRepositoryService(settings)

    def fail_load():
        raise RuntimeError("boom")

    monkeypatch.setattr(service.registry, "load", fail_load)

    repositories, errors = service.snapshot()

    assert repositories == []
    assert errors == ["Git repository inspection failed unexpectedly"]


def test_git_snapshot_cache_reuses_recent_scan(tmp_path: Path, monkeypatch) -> None:
    clear_git_snapshot_cache()
    config = tmp_path / "repositories.yml"
    config.write_text("repositories: []\n", encoding="utf-8")
    settings = Settings(
        enable_git_integration=True,
        repositories_config_path=config,
        git_scan_cache_seconds=60,
    )
    service = GitRepositoryService(settings)
    calls = 0

    original_load = service.registry.load

    def counted_load():
        nonlocal calls
        calls += 1
        return original_load()

    monkeypatch.setattr(service.registry, "load", counted_load)

    assert service.snapshot() == ([], [])
    assert service.snapshot() == ([], [])
    assert calls == 1
