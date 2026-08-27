"""
GIS API test suite for PYRO-SENTRY.
Tests GeoJSON FeatureCollection generation for hotspots, targets, industrial assets, clusters, and risk zones.
"""

import pytest
from fastapi.testclient import TestClient


def test_get_hotspots_gis(client: TestClient):
    """Test retrieving GeoJSON layer of hotspots."""
    response = client.get("/api/v1/gis/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["layer_name"] == "hotspots"
    assert isinstance(data["features"], list)
    assert len(data["features"]) >= 1
    assert data["features"][0]["geometry"]["type"] == "Point"


def test_get_targets_gis(client: TestClient):
    """Test retrieving GeoJSON layer of targets."""
    response = client.get("/api/v1/gis/targets")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["layer_name"] == "targets"
    assert len(data["features"]) >= 1


def test_get_industrial_assets_gis(client: TestClient):
    """Test retrieving GeoJSON layer of industrial infrastructure assets."""
    response = client.get("/api/v1/gis/industrial-assets")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["layer_name"] == "industrial-assets"
    assert len(data["features"]) >= 1


def test_get_clusters_gis(client: TestClient):
    """Test retrieving GeoJSON layer of cluster polygons."""
    response = client.get("/api/v1/gis/clusters")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["layer_name"] == "clusters"


def test_get_risk_zones_gis(client: TestClient):
    """Test retrieving GeoJSON layer of risk zones."""
    response = client.get("/api/v1/gis/risk-zones")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["layer_name"] == "risk-zones"
