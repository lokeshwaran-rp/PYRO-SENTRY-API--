"""
Health & Root API test suite for PYRO-SENTRY.
Validates public access (no auth needed) and application rebranding.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint_public_access(unauth_client: TestClient):
    """Test that /api/v1/health is public and returns 200 without auth."""
    response = unauth_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "PYRO-SENTRY Industrial Thermal Surveillance API"
    assert data["version"] == "2.0.0"
    assert "timestamp" in data
    assert "active_websocket_connections" in data


def test_root_endpoint(unauth_client: TestClient):
    """Test landing root endpoint."""
    response = unauth_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data
