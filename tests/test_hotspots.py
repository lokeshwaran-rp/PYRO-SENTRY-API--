"""
Hotspots API test suite for PYRO-SENTRY.
Tests DB queries, query filters (min_frp, min_confidence, limit), and authentication.
"""

import pytest
from fastapi.testclient import TestClient


def test_list_hotspots_authenticated(client: TestClient):
    """Test retrieving hotspots with valid auth token."""
    response = client.get("/api/v1/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "frp" in data[0]
    assert "confidence" in data[0]
    assert "latitude" in data[0]
    assert "longitude" in data[0]


def test_list_hotspots_unauthenticated(unauth_client: TestClient):
    """Test that hotspots endpoint requires authentication."""
    response = unauth_client.get("/api/v1/hotspots")
    assert response.status_code == 401


def test_list_hotspots_filter_frp(client: TestClient):
    """Test filtering hotspots by minimum FRP."""
    response = client.get("/api/v1/hotspots?min_frp=100.0")
    assert response.status_code == 200
    data = response.json()
    for hs in data:
        assert hs["frp"] >= 100.0


def test_list_hotspots_filter_confidence(client: TestClient):
    """Test filtering hotspots by minimum confidence."""
    response = client.get("/api/v1/hotspots?min_confidence=90.0")
    assert response.status_code == 200
    data = response.json()
    for hs in data:
        assert hs["confidence"] >= 90.0
