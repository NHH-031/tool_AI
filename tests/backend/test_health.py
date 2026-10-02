import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_get_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data
