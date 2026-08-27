from fastapi.testclient import TestClient


def test_gis_hotspots(client: TestClient):
    """Test GET /api/v1/gis/hotspots returns valid GeoJSON FeatureCollection."""
    response = client.get("/api/v1/gis/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) >= 1
    assert data["features"][0]["type"] == "Feature"
    assert data["features"][0]["geometry"]["type"] == "Point"


def test_gis_targets(client: TestClient):
    """Test GET /api/v1/gis/targets returns valid GeoJSON FeatureCollection."""
    response = client.get("/api/v1/gis/targets")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) >= 1


def test_gis_industrial_assets(client: TestClient):
    """Test GET /api/v1/gis/industrial-assets returns valid GeoJSON FeatureCollection."""
    response = client.get("/api/v1/gis/industrial-assets")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) >= 1


def test_gis_clusters(client: TestClient):
    """Test GET /api/v1/gis/clusters returns valid GeoJSON FeatureCollection."""
    response = client.get("/api/v1/gis/clusters")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert data["features"][0]["geometry"]["type"] == "Polygon"


def test_gis_risk_zones(client: TestClient):
    """Test GET /api/v1/gis/risk-zones returns valid GeoJSON FeatureCollection."""
    response = client.get("/api/v1/gis/risk-zones")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert data["features"][0]["geometry"]["type"] == "Polygon"
