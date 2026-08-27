from fastapi.testclient import TestClient


def test_list_targets(client: TestClient):
    """Test listing wildfire targets."""
    response = client.get("/api/v1/targets")
    assert response.status_code == 200
    targets = response.json()
    assert isinstance(targets, list)
    assert len(targets) >= 1
    assert "id" in targets[0]
    assert "name" in targets[0]
    assert "status" in targets[0]


def test_get_target_by_id(client: TestClient):
    """Test retrieving existing target by ID."""
    response = client.get("/api/v1/targets/tgt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "tgt-001"
    assert data["name"] == "Angeles Canyon Hotspot Complex"


def test_get_target_by_id_not_found(client: TestClient):
    """Test 404 for nonexistent target."""
    response = client.get("/api/v1/targets/nonexistent-tgt")
    assert response.status_code == 404


def test_get_target_observations(client: TestClient):
    """Test retrieving target observations."""
    response = client.get("/api/v1/targets/tgt-001/observations")
    assert response.status_code == 200
    observations = response.json()
    assert isinstance(observations, list)
    assert len(observations) >= 1
    assert "sensor" in observations[0]
    assert "frp" in observations[0]


def test_get_target_history(client: TestClient):
    """Test retrieving target audit history."""
    response = client.get("/api/v1/targets/tgt-001/history")
    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
    assert len(history) >= 1
    assert "event" in history[0]
    assert "details" in history[0]


def test_get_target_classification(client: TestClient):
    """Test retrieving target classification breakdown."""
    response = client.get("/api/v1/targets/tgt-001/classification")
    assert response.status_code == 200
    data = response.json()
    assert data["target_id"] == "tgt-001"
    assert "primary_class" in data
    assert "probabilities" in data
    assert data["primary_class"] == "WILDFIRE"


def test_get_target_risk(client: TestClient):
    """Test retrieving target risk assessment."""
    response = client.get("/api/v1/targets/tgt-001/risk")
    assert response.status_code == 200
    data = response.json()
    assert data["target_id"] == "tgt-001"
    assert "risk_score" in data
    assert "risk_category" in data
    assert isinstance(data["threatened_assets"], list)


def test_get_target_evidence(client: TestClient):
    """Test retrieving target multi-source evidence."""
    response = client.get("/api/v1/targets/tgt-001/evidence")
    assert response.status_code == 200
    data = response.json()
    assert data["target_id"] == "tgt-001"
    assert "items" in data
    assert len(data["items"]) >= 1


def test_get_target_satellite(client: TestClient):
    """Test retrieving target satellite metadata and imagery info."""
    response = client.get("/api/v1/targets/tgt-001/satellite")
    assert response.status_code == 200
    data = response.json()
    assert data["target_id"] == "tgt-001"
    assert "satellite" in data
    assert "bands_available" in data
    assert "image_url" in data


def test_target_subresources_404(client: TestClient):
    """Test 404 error responses for all subresources on invalid target ID."""
    invalid_id = "invalid-tgt-999"
    subresources = [
        "observations",
        "history",
        "classification",
        "risk",
        "evidence",
        "satellite",
    ]
    for sub in subresources:
        res = client.get(f"/api/v1/targets/{invalid_id}/{sub}")
        assert res.status_code == 404
