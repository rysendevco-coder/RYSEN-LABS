from app.services.system_metrics import collect_system_metrics


def test_system_metrics_response_shape() -> None:
    metrics = collect_system_metrics()

    assert metrics.hostname
    assert metrics.memory.percent is None or 0 <= metrics.memory.percent <= 100
    assert metrics.disk.percent is None or 0 <= metrics.disk.percent <= 100
    assert isinstance(metrics.unavailable, list)
