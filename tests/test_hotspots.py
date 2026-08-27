from fastapi.testclient import TestClient


def test_get_hotspots(client: TestClient):
    """Test retrieving hotspots list without filters."""
    response = client.get("/api/v1/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "id" in item
    assert "latitude" in item
    assert "longitude" in item
    assert "frp" in item
    assert "confidence" in item


def test_get_hotspots_filtered(client: TestClient):
    """Test retrieving hotspots with query parameter filters."""
    response = client.get("/api/v1/hotspots?min_frp=100.0&min_confidence=90.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert item["frp"] >= 100.0
        assert item["confidence"] >= 90.0
