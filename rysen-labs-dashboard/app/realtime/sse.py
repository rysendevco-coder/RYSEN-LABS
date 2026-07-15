from __future__ import annotations

import json

from pydantic import BaseModel


def format_sse(data: BaseModel | dict[str, object], event: str = "status") -> str:
    if isinstance(data, BaseModel):
        payload = data.model_dump_json()
    else:
        payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n"
