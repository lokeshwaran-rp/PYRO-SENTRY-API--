from fastapi.testclient import TestClient


def test_list_events(client: TestClient):
    """Test retrieving list of events."""
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) >= 1  # Should contain seeded event


def test_create_and_get_event(client: TestClient):
    """Test creating a new wildfire event alert and retrieving it."""
    payload = {
        "title": "Test Ridge Fire",
        "latitude": 34.1234,
        "longitude": -118.5678,
        "severity": "HIGH",
        "source": "UNIT_TEST",
        "description": "Controlled test fire event",
    }
    
    # Create event
    create_resp = client.post("/api/v1/events", json=payload)
    assert create_resp.status_code == 201
    created_event = create_resp.json()
    assert created_event["title"] == payload["title"]
    assert created_event["latitude"] == payload["latitude"]
    assert "id" in created_event
    assert "timestamp" in created_event
    
    event_id = created_event["id"]

    # Get event by id
    get_resp = client.get(f"/api/v1/events/{event_id}")
    assert get_resp.status_code == 200
    fetched_event = get_resp.json()
    assert fetched_event["id"] == event_id
    assert fetched_event["title"] == payload["title"]


def test_get_nonexistent_event(client: TestClient):
    """Test 404 response when requesting non-existent event ID."""
    response = client.get("/api/v1/events/non-existent-id-12345")
    assert response.status_code == 404
