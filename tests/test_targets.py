"""
Targets API test suite for PYRO-SENTRY.
Tests DB queries, sub-resources, and filters on /api/v1/targets.
"""

import pytest
from fastapi.testclient import TestClient


def test_list_targets(client: TestClient):
    """Test retrieving list of targets."""
    response = client.get("/api/v1/targets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "name" in data[0]
    assert "status" in data[0]


def test_list_targets_filter_status(client: TestClient):
    """Test filtering targets by status."""
    response = client.get("/api/v1/targets?status=ACTIVE")
    assert response.status_code == 200
    data = response.json()
    for t in data:
        assert t["status"] == "ACTIVE"


def test_get_target_by_id(client: TestClient):
    """Test retrieving a specific target with embedded sub-resources."""
    response = client.get("/api/v1/targets/tgt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "tgt-001"
    assert "classification" in data
    assert "risk" in data
    assert "evidence" in data
    assert "satellite" in data
    assert "observations" in data
    assert "history" in data


def test_get_target_not_found(client: TestClient):
    """Test 404 for nonexistent target."""
    response = client.get("/api/v1/targets/tgt-999999")
    assert response.status_code == 404


def test_get_target_observations(client: TestClient):
    """Test retrieving target observations subresource."""
    response = client.get("/api/v1/targets/tgt-001/observations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "sensor" in data[0]
    assert "frp" in data[0]


def test_get_target_history(client: TestClient):
    """Test retrieving target history subresource."""
    response = client.get("/api/v1/targets/tgt-001/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "event" in data[0]


def test_get_target_classification(client: TestClient):
    """Test retrieving target classification."""
    response = client.get("/api/v1/targets/tgt-001/classification")
    assert response.status_code == 200
    data = response.json()
    assert "primary_class" in data
    assert "confidence" in data
    assert "probabilities" in data


def test_get_target_risk(client: TestClient):
    """Test retrieving target risk assessment."""
    response = client.get("/api/v1/targets/tgt-001/risk")
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_category" in data


def test_get_target_evidence(client: TestClient):
    """Test retrieving target evidence bundle."""
    response = client.get("/api/v1/targets/tgt-001/evidence")
    assert response.status_code == 200
    data = response.json()
    assert "evidence_count" in data
    assert "items" in data


def test_get_target_satellite(client: TestClient):
    """Test retrieving target satellite pass data."""
    response = client.get("/api/v1/targets/tgt-001/satellite")
    assert response.status_code == 200
    data = response.json()
    assert "satellite" in data
    assert "image_url" in data
