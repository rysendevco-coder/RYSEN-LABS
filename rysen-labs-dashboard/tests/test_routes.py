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
    assert payload["sprint"]["name"] == "Sprint 01 - Ship Something"


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


def test_dashboard_renders_sprint_progress_bars() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="sprint-progress-bar"' in response.text
    assert 'class="progress-fill"' in response.text
    assert "width: 38.9%" in response.text
    assert "width: 47.6%" in response.text


def test_sprint_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/sprint")

    assert response.status_code == 200
    payload = response.json()
    assert payload["progress"]["total_points"] == 36
    assert payload["progress"]["completed_points"] == 14
    assert payload["progress"]["progress_percentage"] == 38.9
    assert payload["progress"]["task_counts"]["blocked"] == 0
    assert payload["schedule"]["expected_progress_percentage"] == 0.0
    assert payload["schedule"]["schedule_status"] == "Ahead of Schedule"


def test_projects_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/projects")

    assert response.status_code == 200
    payload = response.json()
    assert [project["id"] for project in payload] == [
        "rip-or-vault",
        "motorminder",
        "pbct",
        "rysen-labs-infrastructure",
    ]
