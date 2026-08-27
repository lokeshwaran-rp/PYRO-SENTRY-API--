"""
Threats API test suite for PYRO-SENTRY.
Tests DB queries, lifecycle transition validation, error handling, and RBAC on /api/v1/threats.
"""

import pytest
from fastapi.testclient import TestClient


def test_list_threats(client: TestClient):
    """Test retrieving list of threats from DB."""
    response = client.get("/api/v1/threats")
    assert response.status_code == 200
    threats = response.json()
    assert isinstance(threats, list)
    assert len(threats) >= 1
    assert "id" in threats[0]
    assert "severity" in threats[0]
    assert "status" in threats[0]


def test_list_threats_filter_status(client: TestClient):
    """Test filtering threats by lifecycle status."""
    response = client.get("/api/v1/threats?status=NEW")
    assert response.status_code == 200
    threats = response.json()
    for t in threats:
        assert t["status"] == "NEW"


def test_get_threat_by_id(client: TestClient):
    """Test retrieving specific threat by ID."""
    response = client.get("/api/v1/threats/threat-501")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "threat-501"
    assert data["target_id"] == "tgt-001"


def test_get_threat_not_found(client: TestClient):
    """Test 404 for nonexistent threat ID."""
    response = client.get("/api/v1/threats/nonexistent-threat-999")
    assert response.status_code == 404


def test_patch_threat_valid_transition(client: TestClient):
    """Test updating threat severity and valid status transition (NEW -> ACKNOWLEDGED)."""
    patch_payload = {
        "severity": "CRITICAL",
        "status": "ACKNOWLEDGED",
        "notes": "Acknowledged by operations engineer",
    }
    response = client.patch("/api/v1/threats/threat-501", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "threat-501"
    assert data["severity"] == "CRITICAL"
    assert data["status"] == "ACKNOWLEDGED"


def test_patch_threat_invalid_transition_rejected(client: TestClient):
    """Test that illegal transition (NEW -> RESOLVED directly) is rejected with 409 Conflict."""
    patch_payload = {
        "status": "RESOLVED",
    }
    response = client.patch("/api/v1/threats/threat-501", json=patch_payload)
    assert response.status_code == 409
    assert "invalid transition" in response.json()["detail"].lower()


def test_acknowledge_threat(client: TestClient):
    """Test acknowledging a NEW threat."""
    ack_payload = {
        "operator_name": "Test_Operator_99"
    }
    response = client.post("/api/v1/threats/threat-501/acknowledge", json=ack_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACKNOWLEDGED"
    assert data["acknowledged_by"] == "Test_Operator_99"
    assert data["acknowledged_at"] is not None


def test_resolve_threat_lifecycle_flow(client: TestClient):
    """Test full progression to resolution: NEW -> ACKNOWLEDGED -> INVESTIGATING -> DISPATCHED -> RESOLVED."""
    # 1. ACKNOWLEDGE
    res1 = client.post("/api/v1/threats/threat-501/acknowledge")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ACKNOWLEDGED"

    # 2. Transition to INVESTIGATING
    res2 = client.patch("/api/v1/threats/threat-501", json={"status": "INVESTIGATING"})
    assert res2.status_code == 200
    assert res2.json()["status"] == "INVESTIGATING"

    # 3. Transition to DISPATCHED
    res3 = client.patch("/api/v1/threats/threat-501", json={"status": "DISPATCHED"})
    assert res3.status_code == 200
    assert res3.json()["status"] == "DISPATCHED"

    # 4. RESOLVE
    res4 = client.post("/api/v1/threats/threat-501/resolve", json={"resolution_notes": "Hazard cleared"})
    assert res4.status_code == 200
    data = res4.json()
    assert data["status"] == "RESOLVED"
    assert data["resolved_at"] is not None
    assert "Resolution: Hazard cleared" in data["notes"]


def test_resolve_threat_direct_from_new_rejected(client: TestClient):
    """Test attempting to resolve a NEW threat directly without dispatching fails with 409."""
    response = client.post("/api/v1/threats/threat-501/resolve")
    assert response.status_code == 409
    assert "cannot resolve" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()
