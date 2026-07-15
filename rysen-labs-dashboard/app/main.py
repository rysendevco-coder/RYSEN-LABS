from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.logging_config import configure_logging
from app.routes import dashboard, health, realtime, status


APP_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info(
        "dashboard_startup",
        extra={
            "event": "dashboard_startup",
            "safe_mode": settings.safe_mode,
            "docker_enabled": settings.enable_docker_integration,
            "git_enabled": settings.enable_git_integration,
        },
    )

    app = FastAPI(title="Rysen Labs Command Center", version="0.3.0")
    app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
    app.include_router(dashboard.router)
    app.include_router(status.router)
    app.include_router(health.router)
    app.include_router(realtime.router)
    return app


app = create_app()
