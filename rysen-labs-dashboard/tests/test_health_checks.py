import httpx
import pytest

from app.models.schemas import AppConfig, AppHealthState, DockerSnapshot
from app.services.health_checks import check_application


class FakeClient:
    def __init__(self, result):
        self.result = result

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.mark.anyio
async def test_http_health_check_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.health_checks.httpx.AsyncClient",
        lambda **kwargs: FakeClient(httpx.Response(200)),
    )
    app = AppConfig(
        id="ok",
        name="OK",
        description="OK",
        url="http://127.0.0.1",
        internal_health_url="http://127.0.0.1/health",
        health_check_enabled=True,
    )

    health = await check_application(app, DockerSnapshot(enabled=False, available=False), True)

    assert health.state == AppHealthState.HEALTHY
    assert health.http_status == 200


@pytest.mark.anyio
async def test_http_health_check_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.health_checks.httpx.AsyncClient",
        lambda **kwargs: FakeClient(httpx.TimeoutException("timeout")),
    )
    app = AppConfig(
        id="slow",
        name="Slow",
        description="Slow",
        url="http://127.0.0.1",
        internal_health_url="http://127.0.0.1/health",
        health_check_enabled=True,
    )

    health = await check_application(app, DockerSnapshot(enabled=False, available=False), True)

    assert health.state == AppHealthState.UNHEALTHY
    assert health.error == "Health check timed out"


@pytest.mark.anyio
async def test_http_health_check_connection_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.health_checks.httpx.AsyncClient",
        lambda **kwargs: FakeClient(httpx.ConnectError("connection failed")),
    )
    app = AppConfig(
        id="down",
        name="Down",
        description="Down",
        url="http://127.0.0.1",
        internal_health_url="http://127.0.0.1/health",
        health_check_enabled=True,
    )

    health = await check_application(app, DockerSnapshot(enabled=False, available=False), True)

    assert health.state == AppHealthState.UNAVAILABLE
    assert health.error == "Health check connection failed"


@pytest.mark.anyio
async def test_disabled_application_behavior() -> None:
    app = AppConfig(id="disabled", name="Disabled", description="Disabled", url="http://127.0.0.1", enabled=False)

    health = await check_application(app, DockerSnapshot(enabled=False, available=False), True)

    assert health.state == AppHealthState.DISABLED
