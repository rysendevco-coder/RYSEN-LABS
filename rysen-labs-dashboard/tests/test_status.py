from fastapi.testclient import TestClient

from app.main import app


def test_status_endpoint_has_required_sections() -> None:
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["server"]["label"] == "rysen-labs"
    assert "system" in payload
    assert "docker" in payload
    assert len(payload["applications"]) == 7
    assert {card["status"] for card in payload["applications"]} <= {
        "healthy",
        "degraded",
        "stopped",
        "unavailable",
    }
