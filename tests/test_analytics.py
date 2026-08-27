from fastapi.testclient import TestClient


def test_analytics_summary(client: TestClient):
    """Test GET /api/v1/analytics/summary."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "active_targets_count" in data
    assert "total_hotspots_detected_24h" in data
    assert "critical_threats_count" in data
    assert "total_estimated_burned_ha" in data


def test_analytics_frp_trends(client: TestClient):
    """Test GET /api/v1/analytics/frp-trends."""
    response = client.get("/api/v1/analytics/frp-trends")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "timestamp" in data[0]
    assert "total_frp_mw" in data[0]


def test_analytics_classification_distribution(client: TestClient):
    """Test GET /api/v1/analytics/classification-distribution."""
    response = client.get("/api/v1/analytics/classification-distribution")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "WILDFIRE" in data


def test_analytics_hourly_activity(client: TestClient):
    """Test GET /api/v1/analytics/hourly-activity."""
    response = client.get("/api/v1/analytics/hourly-activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 24
    assert "hour_utc" in data[0]
    assert "detections" in data[0]
