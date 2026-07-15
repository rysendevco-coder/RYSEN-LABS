from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.realtime.sse import format_sse
from app.services.status_service import StatusService


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/events")
async def events(request: Request) -> StreamingResponse:
    settings = get_settings()

    async def event_stream():
        logger.info("sse_client_connected", extra={"event": "sse_client_connected"})
        try:
            while not await request.is_disconnected():
                status = await StatusService(settings).dashboard_status()
                yield format_sse(status)
                await asyncio.sleep(settings.update_interval_seconds)
        finally:
            logger.info("sse_client_disconnected", extra={"event": "sse_client_disconnected"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
