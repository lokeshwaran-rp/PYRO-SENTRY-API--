from fastapi.testclient import TestClient


def test_get_satellite_evidence(client: TestClient):
    """Test GET /api/v1/satellite/evidence/{target_id}."""
    response = client.get("/api/v1/satellite/evidence/tgt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["target_id"] == "tgt-001"
    assert "satellite" in data
    assert "swir_anomaly_detected" in data
    assert "preview_thumbnail" in data


def test_get_satellite_evidence_not_found(client: TestClient):
    """Test 404 for nonexistent target satellite evidence."""
    response = client.get("/api/v1/satellite/evidence/nonexistent-target")
    assert response.status_code == 404
