"""
Events API test suite for PYRO-SENTRY.
"""

import pytest
from fastapi.testclient import TestClient


def test_list_events(client: TestClient):
    """Test retrieving list of events."""
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "title" in data[0]
    assert "severity" in data[0]


def test_get_event_by_id(client: TestClient):
    """Test retrieving a specific event."""
    response = client.get("/api/v1/events/evt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "evt-001"


def test_get_event_not_found(client: TestClient):
    """Test 404 for nonexistent event."""
    response = client.get("/api/v1/events/nonexistent-evt-999")
    assert response.status_code == 404


def test_create_event_success(client: TestClient):
    """Test creating a new event by an OPERATOR."""
    payload = {
        "title": "Flare Stack Overpressure Alert",
        "latitude": 29.7200,
        "longitude": -95.0800,
        "severity": "HIGH",
        "source": "FIELD_SENSOR",
        "description": "Pressure relief sensor trigger in Sector 4",
    }
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Flare Stack Overpressure Alert"
    assert data["severity"] == "HIGH"
    assert "id" in data
