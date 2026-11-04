from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] == settings.MODE
    assert "model_info" in data
    assert "provider" in data["model_info"]
    assert "vision_model" in data["model_info"]
    assert "text_model" in data["model_info"]
    assert "family" in data["model_info"]
