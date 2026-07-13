from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import AppCard, get_settings, load_app_cards
from app.logging_config import configure_logging
from app.services.docker_status import collect_docker_status, health_state_for_app
from app.services.system_metrics import collect_system_metrics


configure_logging()

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

app = FastAPI(title="Rysen Labs Command Center", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")


def _cards_with_status(cards: list[AppCard]) -> list[dict[str, object]]:
    docker_snapshot = collect_docker_status()
    return [
        {
            "name": card.name,
            "status": health_state_for_app(card.container_names, docker_snapshot, card.status),
            "url": card.url,
            "description": card.description,
            "category": card.category,
        }
        for card in cards
    ]


def build_status_payload() -> dict[str, object]:
    settings = get_settings()
    system = collect_system_metrics()
    docker_snapshot = collect_docker_status()
    cards = load_app_cards(settings.apps_config_path)
    applications = [
        {
            "name": card.name,
            "status": health_state_for_app(card.container_names, docker_snapshot, card.status),
            "url": card.url,
            "description": card.description,
            "category": card.category,
        }
        for card in cards
    ]
    return {
        "server": {
            "label": settings.host_label,
            "ip": settings.server_ip,
        },
        "system": system.to_dict(),
        "docker": docker_snapshot.to_dict(),
        "applications": applications,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    settings = get_settings()
    payload = build_status_payload()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "title": "Rysen Labs Command Center",
            "refresh_seconds": settings.refresh_seconds,
            "payload": payload,
        },
    )


@app.get("/api/status")
def api_status() -> dict[str, object]:
    return build_status_payload()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rysen-labs-dashboard"}
