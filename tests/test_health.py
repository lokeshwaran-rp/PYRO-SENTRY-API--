from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test GET /api/v1/health returns 200 and healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "timestamp" in data
    assert "active_websocket_connections" in data


def test_root_endpoint(client: TestClient):
    """Test GET / returns welcome payload with links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/v1/health"
