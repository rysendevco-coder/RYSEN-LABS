from app.realtime.sse import format_sse


def test_realtime_event_response_formatting() -> None:
    event = format_sse({"ok": True}, event="status")

    assert event.startswith("event: status\n")
    assert 'data: {"ok": true}' in event
    assert event.endswith("\n\n")
