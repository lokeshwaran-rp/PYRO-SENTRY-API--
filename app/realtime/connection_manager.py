import logging
from typing import List, Any, Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages multiple active WebSocket client connections and handles broadcasting
    structured JSON events across all connected clients.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept incoming connection and register client in active list."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected to /ws. Total active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Unregister client from active list upon disconnection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected from /ws. Total active clients: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a JSON message to a single specific client."""
        await websocket.send_json(message)

    async def broadcast_json(self, message: Dict[str, Any]):
        """
        Broadcast a JSON message to all currently connected clients.
        Stale/broken connections are safely caught and removed.
        """
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning(f"Failed to send to client ({exc}). Marking for cleanup.")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    @property
    def connection_count(self) -> int:
        """Return count of active connected clients."""
        return len(self.active_connections)


# Global singleton instance for connection management across the application
manager = ConnectionManager()
