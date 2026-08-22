# Rysen Labs Dashboard

Rysen Labs Dashboard is a lightweight, read-only operations dashboard for the future `rysen-labs` ZimaBoard at `192.168.50.42`.

Version 0.3 is a local-only, development-host readiness foundation. Do not deploy to the ZimaBoard while its eMMC filesystem is unhealthy or mounted read-only.

## Architecture

- `app/main.py` creates the FastAPI app and registers routes.
- `app/config.py` loads environment-based settings and feature flags.
- `app/models/` contains typed API and configuration models.
- `app/routes/` contains dashboard, status, health, and SSE routes.
- `app/services/system_metrics.py` reads host metrics with graceful fallbacks.
- `app/services/docker_service.py` performs read-only Docker inspection when enabled.
- `app/services/app_registry.py` loads and validates `config/apps.yml`.
- `app/services/repository_registry.py` loads and validates `config/repositories.yml`.
- `app/services/git_service.py` performs read-only Git repository inspection when enabled.
- `app/services/sprint_service.py` loads roadmap YAML and calculates point-weighted sprint progress.
- `app/services/sprint_sync_service.py` validates and archives file-based sprint update inbox entries.
- `app/services/sprint_snapshot_service.py` writes daily sprint progress snapshots on command.
- `app/services/health_checks.py` runs safe concurrent per-app HTTP checks.
- `app/services/status_service.py` assembles the dashboard payload.
- `app/realtime/sse.py` formats Server-Sent Events.
- `app/templates/` and `app/static/` provide the mobile-first UI.

## Local Windows Setup

```powershell
cd <path-to-repository>\rysen-labs-dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

If `python` is not on PATH, use the Codex bundled Python path or your installed Python 3.11+ executable.

## Local Non-Docker Startup

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open `http://localhost:8080`.

## Local Docker Startup

Default mode does not mount the Docker socket:

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f
```

Optional read-only Git repository inspection in a container requires explicitly mounting the repository directories that `config/repositories.yml` references. Do not add personal repository mounts to `docker-compose.yml`; create a local override based on `docker-compose.git.example.yml` and keep repository mounts read-only.

Optional read-only Docker inspection:

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.docker.yml up -d --build
docker compose logs -f
```

## apps.yml Reference

Application cards live in `config/apps.yml`. Supported fields:

- `id`: stable slug used by the dashboard.
- `name`: display name.
- `description`: short card text.
- `category`: grouping label.
- `icon`: future icon hint.
- `url`: browser-facing app URL.
- `internal_health_url`: optional URL used by read-only health checks.
- `container_name`: optional Docker container name.
- `expected_port`: expected service port.
- `enabled`: when false, the card shows disabled.
- `health_check_enabled`: enables HTTP health checks for that app.
- `timeout_seconds`: short per-request timeout.
- `display_order`: lower values appear first.

Legacy v0.1 fields such as `container_names` are still accepted where practical.

## repositories.yml Reference

Repository cards live in `config/repositories.yml`. Git integration is disabled by default and must be enabled with `ENABLE_GIT_INTEGRATION=true`.

Supported fields:

- `id`: stable slug used by the dashboard.
- `name`: display name.
- `description`: short card text.
- `path`: local repository path read by the dashboard process.
- `category`: grouping label.
- `expected_remote`: remote name to display, usually `origin`.
- `default_branch`: expected default branch.
- `enabled`: when false, the repository is not inspected.
- `display_order`: lower values appear first.

The example uses Linux paths for the future ZimaBoard target. For local Windows development, set `REPOSITORIES_CONFIG_PATH` to a local YAML file instead of hardcoding Windows paths into application logic.

Repository inspection is strictly read-only. It uses Git status commands only and never performs pulls, pushes, commits, merges, checkouts, resets, cleans, adds, rebases, or stashes. Enabling this feature allows the dashboard process to read the configured source trees, so only configure paths the dashboard is allowed to inspect.

Ahead/behind counts are relative to the locally known upstream state. The dashboard does not run `git fetch`, so it cannot know whether GitHub or another remote has newer commits until something else updates the local remote-tracking refs.

## Sprint Roadmap Data

Sprint data lives in:

```text
roadmap/
  projects.yaml
  current_sprint.yaml
  updates/
    pending/
    processed/
    rejected/
  history/
```

Edit `roadmap/current_sprint.yaml` to update tasks. Each task supports:

- `id`
- `project`
- `name`
- `description`
- `points`
- `status`
- optional `blocker`
- optional `notes`
- optional `checkpoints`

Supported statuses are `todo`, `in_progress`, `blocked`, and `done`.

Progress is calculated by the backend from sprint points:

```text
completed_points / total_points * 100
```

Only `done` tasks count as completed. Blocked work appears in Needs Attention and does not count as completed.

If a task has checkpoints, checkpoint points must sum to the parent task points and progress is calculated from completed checkpoint points. Schedule health is calculated centrally by the backend from actual progress versus expected linear progress across the sprint date range.

Use `scripts/update_sprint.py` for explicit, safe task/checkpoint status updates. See `docs/SPRINT_SYNC.md` for the standard sprint update contract.

Project repositories can emit verified `sprint_update` files into `roadmap/updates/pending/`. Process them with:

```powershell
python scripts/process_sprint_updates.py --dry-run --all
python scripts/process_sprint_updates.py --apply --file roadmap/updates/pending/rov-update-001.yaml
```

Dry-run never mutates sprint state or moves files. Apply mode is authorized input and may change only the requested task/checkpoint `status`; processed and rejected files are archived for auditability.

Use the PowerShell checkpoint workflow to validate a project checkpoint, capture Git metadata, and emit an inbox update:

```powershell
.\scripts\checkpoint.ps1 -Project rip-or-vault -Task rov-002 -Checkpoint rov-002-e -Status done -RepositoryPath ..\rip-or-vault
```

See `docs/CHECKPOINT_WORKFLOW.md`.

Sprint Auto-Sync V1.2 can commit and push an authorized sprint-state update after the project checkpoint has been validated, committed, pushed, and confirmed synchronized:

```powershell
.\scripts\checkpoint.ps1 `
  -Project rip-or-vault `
  -Task rov-002 `
  -Checkpoint rov-002-e `
  -Status done `
  -RepositoryPath ..\rip-or-vault `
  -ValidationCommand ".\validate.ps1" `
  -Apply `
  -CommitSprintState `
  -PushSprintState
```

Automatic completion to `done` stops if validation is missing, skipped, or failed; if the project repository is dirty; if `git diff --check` fails; if the checkpoint commit is missing; or if the project branch is not synchronized with its upstream.

For verified work outside the active sprint, use `activity_only: true` in the `sprint_update`. Activity-only updates are archived and surfaced as latest project activity, but they do not modify `current_sprint.yaml` or change sprint percentages.

Registered sprint projects include Rip or Vault, MotorMinder, PBCT, Rysen Labs Infrastructure, and Lunch Roulette. Lunch Roulette uses project ID `lunch-roulette` and canonical branch `main`. Registration makes the project ID valid for Sprint Update / Auto-Sync evidence, but Lunch Roulette has no Sprint 01 tasks; status-changing updates for nonexistent active-sprint tasks are intentionally rejected until future sprint scope is added.

Lunch Roulette Checkpoint 8, "Real Google Places Restaurant Provider", completed outside Sprint 01 with commit `4b882661e9f9d652c7b9852865a433011108e59a`. Its evidence is project history only and does not change Sprint 01 points or progress. Recommended Sprint 02 candidate: "Lunch Roulette - Checkpoint 9 - Final Recommendation UX + Live Places Smoke Test."

Create or refresh a daily sprint snapshot with:

```powershell
python scripts/snapshot_sprint.py
```

To start a new sprint, copy the previous `roadmap/current_sprint.yaml` into `roadmap/history/`, then edit `current_sprint.yaml` with the new sprint name, date range, objective, and task list. See `docs/SPRINT_SYSTEM.md`.

Host-side ZimaBoard sync artifacts are included but not installed:

```text
scripts/zima_sync.sh
deploy/systemd/rysen-labs-dashboard-sync.service
deploy/systemd/rysen-labs-dashboard-sync.timer
```

The sync script fetches `origin`, fast-forwards only a clean approved branch, refuses dirty or non-fast-forward states, and never restarts or rebuilds Docker. Install and enable the service/timer only after explicit deployment authorization.

## Environment Variables

- `HOST_LABEL`: display label, default `rysen-labs`.
- `SERVER_IP`: display IP, default `192.168.50.42`.
- `DASHBOARD_HOST`: bind host, default `0.0.0.0`.
- `DASHBOARD_PORT`: bind/published port, default `8080`.
- `DASHBOARD_UPDATE_INTERVAL_SECONDS`: SSE and polling interval, default `30`.
- `ENABLE_DOCKER_INTEGRATION`: default `false`.
- `DOCKER_SOCKET_PATH`: default `unix://var/run/docker.sock`.
- `ENABLE_SERVICE_HEALTH_CHECKS`: default `true`.
- `ENABLE_GIT_INTEGRATION`: default `false`.
- `REPOSITORIES_CONFIG_PATH`: default `config/repositories.yml`.
- `GIT_COMMAND_TIMEOUT_SECONDS`: default `5`.
- `GIT_MAX_REPOSITORIES`: optional limit for configured repository entries.
- `GIT_SCAN_CACHE_SECONDS`: default `15`; avoids spawning Git subprocesses for every live-update request.
- `SAFE_MODE`: default `true`; future management routes must honor this.
- `LOG_LEVEL`: default `INFO`.
- `APPS_CONFIG_PATH`: default `config/apps.yml`.
- `SPRINT_UPDATES_DIR`: default `roadmap/updates`.
- `SPRINT_HISTORY_DIR`: default `roadmap/history`.

## Endpoints

- `GET /` - dashboard UI.
- `GET /api/status` - read-only JSON payload.
- `GET /api/repositories` - read-only repository status list.
- `GET /api/sprint` - current sprint summary, project progress, blockers, and needs-attention tasks.
- `GET /api/sprint/brief` - structured factual sprint brief data.
- `GET /api/projects` - project-level sprint summaries.
- `GET /api/events` - Server-Sent Events stream.
- `GET /health` - container and service health endpoint.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The tests mock external services and do not require the ZimaBoard or Docker daemon.

## Logs

Logs are structured JSON and work well with:

```bash
docker compose logs -f
```

## Future Debian Deployment Procedure

After the ZimaBoard filesystem is healthy:

```bash
cd rysen-labs-dashboard
cp .env.example .env
docker compose up -d --build
curl http://127.0.0.1:8080/health
```

Then open `http://192.168.50.42:8080` from LAN or Tailscale.

## Troubleshooting

- Health checks show unavailable: confirm the app URL, internal health URL, port, and firewall rules.
- Health checks time out: lower network latency or raise `timeout_seconds` cautiously.
- Docker shows disabled: this is the secure default. Use the Docker override file only on a trusted host.
- Docker shows unavailable: check socket path and permissions.
- Git shows disabled: this is the secure default. Enable it only with a repository config and read-only mounts for the repositories being inspected.
- Git ahead/behind looks stale: update local remote-tracking refs outside the dashboard; the dashboard never fetches remotes.
- CPU temperature unavailable: Debian sensor support may need host configuration; the dashboard will still run.

## Security

Keep the dashboard LAN-only or Tailscale-only. Do not expose it through direct router port forwarding. Version 0.3 remains read-only and includes no shell, console, restart, stop, delete, pull, checkout, commit, merge, reset, or update controls.
