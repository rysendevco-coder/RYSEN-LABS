# Project Status

Current version: 0.3.0

## Completed Capabilities

- FastAPI app with server-rendered dashboard and JSON API.
- Read-only system metrics.
- Optional read-only Docker inspection.
- Optional read-only Git repository inspection.
- Read-only repositories API with cached Git scans.
- YAML application registry with validation and legacy compatibility.
- YAML repository registry with validation.
- Concurrent per-application HTTP health checks.
- Server-Sent Events live updates with browser polling fallback.
- Structured JSON logging.
- Hardened Dockerfile and Compose defaults.
- Mobile-first dark command-center UI.
- Sprint update inbox for validated project evidence files.
- PowerShell checkpoint workflow for Git metadata capture and inbox update generation.
- Sprint Auto-Sync V1.2 checkpoint transaction support for verified apply, commit, and push.
- Repository-managed ZimaBoard safe fast-forward sync script and systemd service/timer templates.
- Evidence-only project activity records for verified out-of-sprint checkpoints without changing sprint math.
- Daily sprint snapshot command.
- Structured morning brief endpoint.
- Local test suite that does not require Docker or ZimaBoard access.

## Managed Projects

- Rip or Vault / Collector Command Center (`rip-or-vault`)
- MotorMinder (`motorminder`)
- Powered by Christ & Turbos (`pbct`)
- Rysen Labs Infrastructure (`rysen-labs-infrastructure`)
- Lunch Roulette (`lunch-roulette`)
- Organize Me (`organize-me`)

Lunch Roulette is registered for centralized Sprint Update / Auto-Sync evidence intake. Its canonical development branch is `main`.

Organize Me is registered for centralized Sprint Update / Auto-Sync evidence intake. It currently has no Sprint 01 task points.

## Project History

Rip or Vault / Collector Command Center was reconciled against committed project evidence on 2026-08-22. The following existing Sprint 01 checkpoints were marked done without changing Sprint 01 scope or point totals:

- `rov-002-b` Product selection and metadata population flow. Evidence: Rip or Vault commit `82cb40089fa999e189c00bb1ad3b672c301ad69f`, committed product-selection workflow documentation, API tests, and Flutter widget tests.
- `rov-002-e` Result presentation and error/empty-state behavior. Evidence: Rip or Vault commit `82cb40089fa999e189c00bb1ad3b672c301ad69f`, committed result presentation documentation, diagnostic/error-state coverage, and API/model parsing tests.

Rip or Vault Decision Engine / D1 internal testing work was also recorded as latest verified activity. Work that did not exactly satisfy an existing Sprint 01 checkpoint was not retroactively added to the sprint.

Lunch Roulette Checkpoint 8, "Real Google Places Restaurant Provider", completed outside Sprint 01 tracking and should not be added retroactively to Sprint 01 totals. Verified evidence:

- Commit: `4b882661e9f9d652c7b9852865a433011108e59a`
- Remote: `origin/main`
- Git divergence after completion: `0 / 0`
- JVM tests: `91 passed`
- `lintDebug`: passed
- `assembleDebug`: passed
- `assembleDebugAndroidTest`: passed
- `git diff --check`: passed
- Credential scan: clear
- Merged manifest: coarse location only
- Live Places smoke test: not yet performed

Recommended Sprint 02 candidate: Lunch Roulette - Checkpoint 9 - Final Recommendation UX + Live Places Smoke Test. Suggested scope is polishing the selected restaurant recommendation/result experience, preserving the app as a roulette/recommendation tool, and validating real-device Places behavior with a properly restricted debug key.

MotorMinder's committed Modifications CRUD APEX checkpoint was recorded as latest verified activity at commit `b525c0e976cd92165a8b7f26ba1533095aca95e1`. Newer Garage Files work was visible locally but uncommitted, so it was not counted as verified activity.

PBCT's APEX About / Mission page capture was recorded as latest verified activity at commit `562b7da5868c1cb3147979f9045ebe93c5007cb1`. The current dirty export was not counted as verified activity.

Organize Me's local Android catalog application baseline was recorded as observed activity based on filesystem inspection. No standalone Git commit was available in the inspected project directory, so this is intentionally lower-confidence than committed checkpoint evidence.

## Architecture Summary

The application is organized around small services and route modules. Configuration, app registry loading, Docker inspection, system metrics, health checks, status assembly, SSE formatting, and FastAPI routes are separate modules.

## Tests And Validation Status

Latest local validation:

```text
.\.venv\Scripts\python.exe -m pytest
27 passed, 1 warning

.\.venv\Scripts\python.exe -m compileall app tests
Passed

git diff --check
Passed with Git line-ending warnings only

docker compose config
Passed with Docker config-file access warnings only

docker compose -f docker-compose.yml -f docker-compose.docker.yml config
Passed with Docker config-file access warnings only

docker info --format '{{.ServerVersion}}'
Docker daemon unavailable; container runtime smoke test not performed
```

The warning comes from FastAPI/Starlette test client dependency guidance.

## Known Limitations

- No authentication yet.
- No database persistence.
- Historical sprint snapshots are command-generated only; no scheduler is installed.
- ZimaBoard sync artifacts are prepared but not installed or enabled.
- Health checks are point-in-time checks only.
- Docker inspection is optional and disabled by default.
- Git inspection is optional and disabled by default.
- Git ahead/behind state may be stale without an external `git fetch`; the dashboard does not update remote-tracking refs.
- CPU temperature depends on host sensor support.

## Deployment Blockers

- The target ZimaBoard eMMC filesystem is unhealthy and mounted read-only.
- Do not deploy until the server storage is replaced or otherwise repaired.

## Security Risks

- LAN-only/Tailscale-only access is required.
- Docker socket access remains sensitive if the optional override is enabled.
- Repository inspection can read configured source trees when enabled.
- Authentication must be designed before any broader exposure.

## Deferred Features

- Authentication and roles.
- Container management controls.
- Shell or console access.
- Automatic image updates.
- Repository action controls.
- GitHub Actions deployment.
- Cloudflare Tunnel.
- Alerting integrations.
- Databases.
- AI integrations.
- Automatic sprint update generation from GitHub or project repositories.
- CasaOS write operations.

## Recommended Next Phase

After the ZimaBoard filesystem is healthy, run a local Docker smoke test on the server without Docker socket access, then validate optional Docker inspection with the override file.
