"""
System status API test suite for PYRO-SENTRY.
"""

import pytest
from fastapi.testclient import TestClient


def test_get_data_sources(client: TestClient):
    """Test retrieving telemetry and ingestion data sources status."""
    response = client.get("/api/v1/system/data-sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "name" in data[0]
    assert "status" in data[0]


def test_get_system_status(client: TestClient):
    """Test retrieving overall system metrics and component health."""
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "system_name" in data
    assert "status" in data
    assert "active_modules" in data
    assert "uptime_seconds" in data
    assert "memory_usage_mb" in data
    assert "cpu_load_pct" in data
