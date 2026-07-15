from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.models.schemas import DashboardStatus, RepositoryStatus
from app.services.status_service import StatusService


router = APIRouter()


@router.get("/api/status", response_model=DashboardStatus)
async def api_status() -> DashboardStatus:
    return await StatusService(get_settings()).dashboard_status()


@router.get("/api/repositories", response_model=list[RepositoryStatus])
async def api_repositories() -> list[RepositoryStatus]:
    status = await StatusService(get_settings()).dashboard_status()
    return status.repositories
