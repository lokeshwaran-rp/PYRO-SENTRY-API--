from fastapi.testclient import TestClient
from app.main import app


def test_websocket_connection_and_echo():
    """Test connecting to WebSocket and sending/receiving messages."""
    client = TestClient(app)
    with client.websocket_connect("/ws/realtime") as websocket:
        # First message should be connection established
        welcome_data = websocket.receive_json()
        assert welcome_data["type"] == "CONNECTION_ESTABLISHED"
        assert "Connected to PYRO-SENTRY" in welcome_data["message"]

        # Send test message to trigger echo
        websocket.send_text("PING")
        echo_data = websocket.receive_json()
        assert echo_data["type"] == "ECHO"
        assert echo_data["received"] == "PING"


def test_websocket_receives_broadcast_event():
    """Test that connected WebSocket client receives alerts broadcasted from REST API."""
    client = TestClient(app)
    with client.websocket_connect("/ws/realtime") as websocket:
        # Consume welcome message
        welcome = websocket.receive_json()
        assert welcome["type"] == "CONNECTION_ESTABLISHED"

        # Trigger event creation in another client call
        event_payload = {
            "title": "WebSocket Realtime Broadcast Test",
            "latitude": 36.1699,
            "longitude": -115.1398,
            "severity": "CRITICAL",
            "source": "WS_TEST",
            "description": "Testing realtime WS broadcast propagation",
        }
        res = client.post("/api/v1/events", json=event_payload)
        assert res.status_code == 201

        # WebSocket should immediately receive the WILDFIRE_ALERT
        alert_msg = websocket.receive_json()
        assert alert_msg["type"] == "WILDFIRE_ALERT"
        assert alert_msg["data"]["title"] == "WebSocket Realtime Broadcast Test"
        assert alert_msg["data"]["severity"] == "CRITICAL"
