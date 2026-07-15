from docker.errors import DockerException

from app.config import Settings
from app.services.docker_service import DockerService


def test_docker_disabled_behavior() -> None:
    snapshot = DockerService(Settings(enable_docker_integration=False)).snapshot()

    assert snapshot.enabled is False
    assert snapshot.available is False
    assert snapshot.error == "Docker integration disabled"


def test_docker_unavailable_behavior(monkeypatch) -> None:
    def raise_unavailable(*args, **kwargs):
        raise DockerException("no socket")

    monkeypatch.setattr("app.services.docker_service.docker.DockerClient", raise_unavailable)

    snapshot = DockerService(Settings(enable_docker_integration=True)).snapshot()

    assert snapshot.enabled is True
    assert snapshot.available is False
    assert snapshot.error == "Docker socket unavailable"
