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
- Daily sprint snapshot command.
- Structured morning brief endpoint.
- Local test suite that does not require Docker or ZimaBoard access.

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
