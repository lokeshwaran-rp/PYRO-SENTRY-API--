from fastapi.testclient import TestClient


def test_list_threats(client: TestClient):
    """Test retrieving list of threats."""
    response = client.get("/api/v1/threats")
    assert response.status_code == 200
    threats = response.json()
    assert isinstance(threats, list)
    assert len(threats) >= 1
    assert "id" in threats[0]
    assert "severity" in threats[0]
    assert "status" in threats[0]


def test_get_threat_by_id(client: TestClient):
    """Test retrieving threat by ID."""
    response = client.get("/api/v1/threats/threat-501")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "threat-501"
    assert data["target_id"] == "tgt-001"


def test_get_threat_not_found(client: TestClient):
    """Test 404 for invalid threat ID."""
    response = client.get("/api/v1/threats/invalid-threat-id")
    assert response.status_code == 404


def test_patch_threat(client: TestClient):
    """Test updating threat severity and notes."""
    patch_payload = {
        "severity": "CRITICAL",
        "notes": "Updated via pytest automated test run.",
    }
    response = client.patch("/api/v1/threats/threat-501", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "threat-501"
    assert data["severity"] == "CRITICAL"
    assert data["notes"] == "Updated via pytest automated test run."


def test_acknowledge_threat(client: TestClient):
    """Test acknowledging a threat."""
    ack_payload = {
        "operator_name": "Test_Operator_99"
    }
    response = client.post("/api/v1/threats/threat-501/acknowledge", json=ack_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACKNOWLEDGED"
    assert data["acknowledged_by"] == "Test_Operator_99"
    assert data["acknowledged_at"] is not None


def test_resolve_threat(client: TestClient):
    """Test resolving a threat."""
    resolve_payload = {
        "resolution_notes": "Hazard eliminated by containment line."
    }
    response = client.post("/api/v1/threats/threat-501/resolve", json=resolve_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"
    assert data["resolved_at"] is not None
    assert "Resolution: Hazard eliminated by containment line." in data["notes"]


def test_threat_actions_not_found(client: TestClient):
    """Test 404 for patch, ack, and resolve on nonexistent threat."""
    bad_id = "nonexistent-threat-999"
    assert client.patch(f"/api/v1/threats/{bad_id}", json={"severity": "LOW"}).status_code == 404
    assert client.post(f"/api/v1/threats/{bad_id}/acknowledge").status_code == 404
    assert client.post(f"/api/v1/threats/{bad_id}/resolve").status_code == 404
