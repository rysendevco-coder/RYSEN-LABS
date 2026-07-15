from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.3.0"


def test_status_endpoint_has_required_sections() -> None:
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["server"]["label"] == "rysen-labs"
    assert "system" in payload
    assert "docker" in payload
    assert "generated_at" in payload
    assert len(payload["applications"]) == 7
    assert payload["repositories"] == []
    assert payload["docker"]["enabled"] is False


def test_repositories_endpoint_is_safe_when_git_disabled() -> None:
    client = TestClient(app)

    response = client.get("/api/repositories")

    assert response.status_code == 200
    assert response.json() == []


def test_safe_startup_without_docker_socket() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Rysen Labs Command Center" in response.text
