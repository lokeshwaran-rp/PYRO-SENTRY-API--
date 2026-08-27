from fastapi.testclient import TestClient


def test_system_data_sources(client: TestClient):
    """Test GET /api/v1/system/data-sources."""
    response = client.get("/api/v1/system/data-sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "name" in data[0]
    assert "status" in data[0]
    assert "ping_ms" in data[0]


def test_system_status(client: TestClient):
    """Test GET /api/v1/system/status."""
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "uptime_seconds" in data
    assert "pipeline_latency_ms" in data
    assert isinstance(data["active_modules"], list)
