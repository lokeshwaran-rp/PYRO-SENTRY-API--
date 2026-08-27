import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Realtime WebSocket"])


async def _handle_websocket_client(websocket: WebSocket):
    """Common handler for WebSocket client lifecycle and bidirectional message flow."""
    await manager.connect(websocket)
    try:
        # Initial connection acknowledgment message with both 'event' and 'type' for compatibility
        await manager.send_personal_message(
            {
                "event": "connection.established",
                "type": "CONNECTION_ESTABLISHED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Connected to PYRO-SENTRY Realtime WebSocket (/ws)",
                "active_clients": manager.connection_count,
                "client_count": manager.connection_count,
            },
            websocket,
        )

        # Listen for client frames (ping/pong, client subscriptions, or echoes)
        while True:
            raw_text = await websocket.receive_text()
            try:
                parsed = json.loads(raw_text)
            except Exception:
                parsed = {"raw": raw_text}

            # Respond with echo/ack
            await manager.send_personal_message(
                {
                    "event": "client.echo",
                    "type": "ECHO",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "received": raw_text if not isinstance(parsed, dict) or "raw" in parsed else parsed,
                },
                websocket,
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.warning(f"WebSocket client error: {exc}")
        manager.disconnect(websocket)


@router.websocket("/ws")
async def websocket_endpoint_root(websocket: WebSocket):
    """
    Primary WebSocket endpoint at `/ws` for receiving realtime wildfire telemetry and alerts.
    
    Supported Broadcast Events:
    - `hotspot.created`
    - `target.updated`
    - `classification.completed`
    - `risk.updated`
    - `threat.created`
    - `threat.updated`
    - `simulation.completed`
    - `system.status`
    """
    await _handle_websocket_client(websocket)


@router.websocket("/ws/realtime")
async def websocket_endpoint_alias(websocket: WebSocket):
    """Alias WebSocket route for backward compatibility."""
    await _handle_websocket_client(websocket)
