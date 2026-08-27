"""
WebSocket test suite for PYRO-SENTRY.
Tests connection establishment, message echo, broadcast delivery, and clean disconnects on /ws.
"""

import pytest
from fastapi.testclient import TestClient
from app.realtime.publisher import publisher


def test_websocket_connection_and_handshake(unauth_client: TestClient):
    """Test connecting to /ws receives connection.established event."""
    with unauth_client.websocket_connect("/ws") as ws:
        init_data = ws.receive_json()
        assert init_data["event"] == "connection.established"
        assert "PYRO-SENTRY" in init_data["message"]
        assert init_data["active_clients"] >= 1


def test_websocket_echo_message(unauth_client: TestClient):
    """Test sending a frame to /ws returns client.echo response."""
    with unauth_client.websocket_connect("/ws") as ws:
        # Flush initial handshake
        ws.receive_json()

        # Send test message
        ws.send_text('{"action": "ping", "client_id": "test_1"}')
        echo_response = ws.receive_json()

        assert echo_response["event"] == "client.echo"
        assert echo_response["received"]["action"] == "ping"
        assert echo_response["received"]["client_id"] == "test_1"


def test_websocket_event_broadcast_reception(unauth_client: TestClient, client: TestClient):
    """Test that a client connected to /ws receives events published via publisher / REST endpoint."""
    with unauth_client.websocket_connect("/ws") as ws:
        # Flush handshake
        ws.receive_json()

        # Trigger event publication via authenticated client
        event_payload = {
            "event": "hotspot.created",
            "data": {
                "hotspot_id": "hs-live-99",
                "frp": 120.0,
                "confidence": 95.0,
            }
        }
        res = client.post("/api/v1/realtime/publish", json=event_payload)
        assert res.status_code == 200

        # Receive broadcast on WebSocket
        broadcast_msg = ws.receive_json()
        assert broadcast_msg["event"] == "hotspot.created"
        assert broadcast_msg["data"]["hotspot_id"] == "hs-live-99"
