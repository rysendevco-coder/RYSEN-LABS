from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from pathlib import Path
import shutil
import subprocess
import threading
import time
from urllib.parse import urlsplit, urlunsplit

from app.config import Settings
from app.models.schemas import RepositoryConfig, RepositoryStatus, RepositoryStatusClass
from app.services.repository_registry import RepositoryRegistry


logger = logging.getLogger(__name__)

MAX_GIT_OUTPUT_CHARS = 20_000

_CACHE_LOCK = threading.Lock()
_SNAPSHOT_CACHE: dict[tuple[str, str, int | None, float], tuple[float, list[RepositoryStatus], list[str]]] = {}


@dataclass(frozen=True)
class GitResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


class GitRepositoryService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.registry = RepositoryRegistry(
            settings.repositories_config_path,
            settings.git_max_repositories,
        )
        self.git_executable = shutil.which("git")

    def snapshot(self) -> tuple[list[RepositoryStatus], list[str]]:
        if not self.settings.enable_git_integration:
            return [], []

        cache_key = (
            str(self.settings.repositories_config_path.resolve(strict=False)),
            str(self.git_executable),
            self.settings.git_max_repositories,
            self.settings.git_command_timeout_seconds,
        )
        if self.settings.git_scan_cache_seconds > 0:
            with _CACHE_LOCK:
                cached = _SNAPSHOT_CACHE.get(cache_key)
            if cached and time.monotonic() - cached[0] < self.settings.git_scan_cache_seconds:
                return cached[1], cached[2]

        try:
            repositories, errors = self.registry.load()
            statuses = [self.repository_status(repository) for repository in repositories]
        except Exception:
            logger.exception("git_snapshot_failed", extra={"event": "git_snapshot_failed"})
            return [], ["Git repository inspection failed unexpectedly"]

        if self.settings.git_scan_cache_seconds > 0:
            with _CACHE_LOCK:
                _SNAPSHOT_CACHE[cache_key] = (time.monotonic(), statuses, errors)
        return statuses, errors

    def repository_status(self, repository: RepositoryConfig) -> RepositoryStatus:
        now = datetime.now(timezone.utc)
        base = {
            "enabled": repository.enabled,
            "repository_name": repository.name,
            "path": str(repository.path),
            "category": repository.category,
            "remote_name": repository.expected_remote,
            "expected_default_branch": repository.default_branch,
            "last_checked_at": now,
            "display_order": repository.display_order,
        }

        if not repository.enabled:
            return RepositoryStatus(
                **base,
                status_class=RepositoryStatusClass.DISABLED,
                warning="Repository is disabled in configuration",
            )

        if self.git_executable is None:
            return RepositoryStatus(
                **base,
                status_class=RepositoryStatusClass.UNAVAILABLE,
                warning="Git executable is not available",
            )

        if not repository.path.exists():
            return RepositoryStatus(
                **base,
                status_class=RepositoryStatusClass.MISSING,
                warning="Repository path does not exist",
            )

        if not repository.path.is_dir():
            return RepositoryStatus(
                **base,
                path_exists=True,
                status_class=RepositoryStatusClass.INVALID,
                warning="Repository path is not a directory",
            )

        inside_work_tree = self._git(repository.path, ["rev-parse", "--is-inside-work-tree"])
        if not inside_work_tree.ok or inside_work_tree.stdout.strip() != "true":
            return RepositoryStatus(
                **base,
                path_exists=True,
                status_class=RepositoryStatusClass.INVALID,
                warning=self._safe_error(inside_work_tree, "Path is not a Git repository"),
            )

        branch_result = self._git(repository.path, ["branch", "--show-current"])
        commit_result = self._git(repository.path, ["rev-parse", "HEAD"])
        log_result = self._git(repository.path, ["log", "-1", "--format=%cI%x00%s"])
        upstream_result = self._git(repository.path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        remote_url_result = self._git(
            repository.path,
            ["remote", "get-url", repository.expected_remote or "origin"],
        )
        tag_result = self._git(repository.path, ["describe", "--tags", "--always", "--dirty"])
        status_result = self._git(repository.path, ["status", "--porcelain=v1", "-b"])
        ahead_behind = self._ahead_behind(repository.path, upstream_result.stdout.strip() if upstream_result.ok else None)

        detached = not branch_result.stdout.strip()
        commit = commit_result.stdout.strip() if commit_result.ok else None
        latest_timestamp: datetime | None = None
        latest_message: str | None = None
        if log_result.ok and "\x00" in log_result.stdout:
            raw_timestamp, latest_message = log_result.stdout.split("\x00", 1)
            try:
                latest_timestamp = datetime.fromisoformat(raw_timestamp.strip().replace("Z", "+00:00"))
            except ValueError:
                latest_timestamp = None
            latest_message = latest_message.strip()[:500]

        status_counts = self._status_counts(status_result.stdout if status_result.ok else "")
        status_class = self._classify(
            detached=detached,
            conflicted_files=status_counts["conflicted"],
            working_tree_clean=status_counts["dirty"] == 0,
            ahead_count=ahead_behind[0],
            behind_count=ahead_behind[1],
        )

        warning = None
        for result, fallback in [
            (commit_result, "Could not read current commit"),
            (status_result, "Could not read working tree status"),
        ]:
            if not result.ok:
                warning = self._safe_error(result, fallback)
                status_class = RepositoryStatusClass.UNAVAILABLE
                break

        return RepositoryStatus(
            **base,
            path_exists=True,
            valid_git_repository=True,
            current_branch=branch_result.stdout.strip() or None,
            detached_head=detached,
            current_commit_sha=commit,
            short_commit_sha=commit[:7] if commit else None,
            latest_commit_message=latest_message,
            latest_commit_timestamp=latest_timestamp,
            remote_url=sanitize_remote_url(remote_url_result.stdout.strip()) if remote_url_result.ok else None,
            working_tree_clean=status_counts["dirty"] == 0,
            modified_files=status_counts["modified"],
            staged_files=status_counts["staged"],
            untracked_files=status_counts["untracked"],
            conflicted_files=status_counts["conflicted"],
            ahead_count=ahead_behind[0],
            behind_count=ahead_behind[1],
            upstream_branch=upstream_result.stdout.strip() if upstream_result.ok else None,
            tag_or_version=tag_result.stdout.strip()[:200] if tag_result.ok else None,
            warning=warning,
            status_class=status_class,
        )

    def _git(self, cwd: Path, args: list[str]) -> GitResult:
        if self.git_executable is None:
            return GitResult(ok=False, stderr="Git executable is not available")
        try:
            completed = subprocess.run(
                [self.git_executable, *args],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=self.settings.git_command_timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            logger.warning("git_command_timeout", extra={"event": "git_command_timeout", "git_args": args[:2]})
            return GitResult(ok=False, stderr="Git command timed out", timed_out=True)
        except OSError as exc:
            logger.warning("git_command_failed", extra={"event": "git_command_failed", "git_args": args[:2]})
            return GitResult(ok=False, stderr=str(exc))

        stdout = (completed.stdout or "")[:MAX_GIT_OUTPUT_CHARS]
        stderr = (completed.stderr or "")[:MAX_GIT_OUTPUT_CHARS]
        return GitResult(ok=completed.returncode == 0, stdout=stdout, stderr=stderr)

    def _ahead_behind(self, cwd: Path, upstream: str | None) -> tuple[int | None, int | None]:
        if not upstream:
            return None, None
        result = self._git(cwd, ["rev-list", "--left-right", "--count", f"HEAD...{upstream}"])
        if not result.ok:
            return None, None
        parts = result.stdout.strip().split()
        if len(parts) != 2:
            return None, None
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None, None

    @staticmethod
    def _status_counts(output: str) -> dict[str, int]:
        counts = {"dirty": 0, "modified": 0, "staged": 0, "untracked": 0, "conflicted": 0}
        for line in output.splitlines():
            if not line or line.startswith("##"):
                continue
            counts["dirty"] += 1
            if line.startswith("??"):
                counts["untracked"] += 1
                continue
            index_status = line[0]
            worktree_status = line[1] if len(line) > 1 else " "
            if index_status in {"A", "M", "D", "R", "C"}:
                counts["staged"] += 1
            if worktree_status in {"M", "D"}:
                counts["modified"] += 1
            if index_status == "U" or worktree_status == "U" or (index_status, worktree_status) in {
                ("A", "A"),
                ("D", "D"),
            }:
                counts["conflicted"] += 1
        return counts

    @staticmethod
    def _classify(
        *,
        detached: bool,
        conflicted_files: int,
        working_tree_clean: bool,
        ahead_count: int | None,
        behind_count: int | None,
    ) -> RepositoryStatusClass:
        if conflicted_files:
            return RepositoryStatusClass.CONFLICTED
        if detached:
            return RepositoryStatusClass.DETACHED
        if ahead_count and behind_count:
            return RepositoryStatusClass.DIVERGED
        if ahead_count:
            return RepositoryStatusClass.AHEAD
        if behind_count:
            return RepositoryStatusClass.BEHIND
        if not working_tree_clean:
            return RepositoryStatusClass.DIRTY
        return RepositoryStatusClass.HEALTHY

    @staticmethod
    def _safe_error(result: GitResult, fallback: str) -> str:
        message = result.stderr.strip() or fallback
        return sanitize_remote_url(message.splitlines()[0][:300])


def sanitize_remote_url(value: str | None) -> str | None:
    if not value:
        return value
    value = value.strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        return _sanitize_scp_like_url(value)
    if parsed.scheme and parsed.netloc:
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))
    return _sanitize_scp_like_url(value)


def _sanitize_scp_like_url(value: str) -> str:
    if "@" in value and ":" in value:
        prefix, rest = value.split("@", 1)
        if ":" in rest and "/" not in prefix:
            return rest
    return value


def clear_git_snapshot_cache() -> None:
    with _CACHE_LOCK:
        _SNAPSHOT_CACHE.clear()
