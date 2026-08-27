from fastapi.testclient import TestClient
from app.main import app
from app.realtime.connection_manager import manager
from app.realtime.publisher import publisher, SUPPORTED_EVENT_TYPES


def test_websocket_connection():
    """Test connecting to /ws endpoint and receiving initial handshake."""
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        msg = ws.receive_json()
        assert msg["event"] == "connection.established"
        assert "Connected to PYRO-SENTRY" in msg["message"]
        assert msg["active_clients"] >= 1


def test_websocket_disconnection():
    """Test that connection manager accurately decrements active client count upon disconnection."""
    client = TestClient(app)
    initial_count = manager.connection_count

    with client.websocket_connect("/ws") as ws:
        # Connected
        assert manager.connection_count == initial_count + 1
        _ = ws.receive_json()

    # Disconnected after context exit
    assert manager.connection_count == initial_count


def test_websocket_sending_and_receiving_event():
    """Test event publisher broadcasting an event and receiving on /ws."""
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        _ = ws.receive_json()  # connection.established

        # Trigger event via REST publish endpoint
        event_payload = {
            "event": "hotspot.created",
            "data": {
                "hotspot_id": "hs-test-01",
                "latitude": 34.250,
                "longitude": -118.170,
                "frp": 145.0,
                "confidence": 96.0,
            },
        }
        res = client.post("/api/v1/realtime/publish", json=event_payload)
        assert res.status_code == 200

        # Verify event received on websocket
        received = ws.receive_json()
        assert received["event"] == "hotspot.created"
        assert "timestamp" in received
        assert received["data"]["hotspot_id"] == "hs-test-01"
        assert received["data"]["frp"] == 145.0


def test_websocket_multiple_clients():
    """Test broadcasting to multiple concurrent WebSocket clients simultaneously."""
    client = TestClient(app)
    
    with client.websocket_connect("/ws") as ws1, client.websocket_connect("/ws") as ws2, client.websocket_connect("/ws") as ws3:
        # Consume handshakes for all 3 clients
        _ = ws1.receive_json()
        _ = ws2.receive_json()
        _ = ws3.receive_json()

        # Publish a threat.created event
        threat_payload = {
            "event": "threat.created",
            "data": {
                "threat_id": "threat-test-99",
                "severity": "CRITICAL",
                "title": "Corridor Hazard",
            },
        }
        res = client.post("/api/v1/realtime/publish", json=threat_payload)
        assert res.status_code == 200

        # All 3 clients must receive the broadcasted event
        msg1 = ws1.receive_json()
        msg2 = ws2.receive_json()
        msg3 = ws3.receive_json()

        for msg in [msg1, msg2, msg3]:
            assert msg["event"] == "threat.created"
            assert msg["data"]["threat_id"] == "threat-test-99"
            assert msg["data"]["severity"] == "CRITICAL"


def test_all_supported_event_types():
    """Test publishing all 8 required event types to /ws."""
    client = TestClient(app)
    expected_event_types = [
        "hotspot.created",
        "target.updated",
        "classification.completed",
        "risk.updated",
        "threat.created",
        "threat.updated",
        "simulation.completed",
        "system.status",
    ]

    with client.websocket_connect("/ws") as ws:
        _ = ws.receive_json()  # handshake

        for event_name in expected_event_types:
            pub_res = client.post(
                "/api/v1/realtime/publish",
                json={"event": event_name, "data": {"test_key": f"value_for_{event_name}"}},
            )
            assert pub_res.status_code == 200

            event_frame = ws.receive_json()
            assert event_frame["event"] == event_name
            assert event_frame["data"]["test_key"] == f"value_for_{event_name}"


def test_publish_unsupported_event_type_rejected():
    """Test 400 Bad Request when attempting to publish an unsupported event type."""
    client = TestClient(app)
    bad_payload = {
        "event": "unsupported.random.event",
        "data": {"foo": "bar"},
    }
    res = client.post("/api/v1/realtime/publish", json=bad_payload)
    assert res.status_code == 400
    assert "Unsupported event type" in res.json()["detail"]
