# Rysen Labs Dashboard

Rysen Labs Dashboard is a lightweight, read-only operations dashboard for the `rysen-labs` ZimaBoard at `192.168.50.42`.

It uses FastAPI, server-rendered Jinja templates, vanilla JavaScript, Docker Compose, and YAML configuration. Version 0.1 has no cloud dependencies and is designed to run comfortably on an Intel Celeron N3450 with 8 GB RAM.

## Features

- Hostname, uptime, CPU usage, load average, memory usage, disk usage, and CPU temperature when available.
- Docker container status through the Docker socket.
- Editable application cards from `config/apps.yml`.
- Health states: `healthy`, `degraded`, `stopped`, and `unavailable`.
- Polished dark mobile-first UI for Galaxy Z Fold 6, phones, tablets, and desktop.
- Read-only v0.1 surface: no shell execution, no restart controls, and no destructive operations.
- Structured JSON logs.

## Local Development

```powershell
cd rysen-labs-dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open `http://localhost:8080`.

On Windows, Docker and load average may show as unavailable depending on the local environment. The app is expected to degrade gracefully.

## ZimaBoard Deployment

Run these commands on `rysen-labs` after copying or cloning this project to the server:

```bash
cd rysen-labs-dashboard
cp .env.example .env
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8080/health
```

Then open `http://192.168.50.42:8080` from a LAN or Tailscale-connected device.

## Editing Application Cards

Edit `config/apps.yml`, then restart the container:

```bash
docker compose restart rysen-labs-dashboard
```

Each card supports:

- `name`
- `status`
- `url`
- `description`
- `category`
- `container_names`

When `container_names` are present and Docker is available, runtime Docker status overrides the configured status.

## Endpoints

- `GET /` - dashboard UI.
- `GET /api/status` - read-only JSON dashboard payload.
- `GET /health` - service health check.

## Security Boundaries

- No command execution routes.
- No Docker mutation routes.
- No frontend exposure of environment variables or secrets.
- Docker socket access is used only for read-only inspection in application code.
- The Docker socket is sensitive even when mounted read-only. See `SECURITY.md`.
