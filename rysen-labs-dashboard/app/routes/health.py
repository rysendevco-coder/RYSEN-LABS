from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "rysen-labs-dashboard", "version": "0.3.0"}
