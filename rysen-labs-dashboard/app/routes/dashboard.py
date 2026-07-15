from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.services.status_service import StatusService


APP_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    settings = get_settings()
    payload = await StatusService(settings).dashboard_status()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "title": "Rysen Labs Command Center",
            "update_interval_seconds": settings.update_interval_seconds,
            "payload": payload.model_dump(mode="json"),
        },
    )
