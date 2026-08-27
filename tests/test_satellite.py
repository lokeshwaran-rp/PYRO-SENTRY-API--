"""
Satellite Evidence API test suite for PYRO-SENTRY.
"""

import pytest
from fastapi.testclient import TestClient


def test_get_target_satellite_evidence(client: TestClient):
    """Test retrieving satellite evidence for a target."""
    response = client.get("/api/v1/satellite/evidence/tgt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["target_id"] == "tgt-001"
    assert "satellite" in data
    assert "acquisition_time" in data
    assert "spatial_resolution" in data
    assert "swir_anomaly_detected" in data
    assert "swir_band_max_value" in data
    assert "overlay_geojson_url" in data


def test_get_satellite_evidence_not_found(client: TestClient):
    """Test 404 for unknown target ID."""
    response = client.get("/api/v1/satellite/evidence/nonexistent-tgt")
    assert response.status_code == 404
