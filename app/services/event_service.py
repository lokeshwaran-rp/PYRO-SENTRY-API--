import uuid
from datetime import datetime, timezone
from typing import List, Optional
from app.schemas.event import WildfireEventCreate, WildfireEventResponse
from app.realtime.connection_manager import manager


class EventService:
    """
    In-memory service managing wildfire alerts and broadcasting newly reported
    events over the Realtime WebSocket.
    """

    def __init__(self):
        self._events: List[WildfireEventResponse] = []
        # Prepopulate with a sample event for instant visibility
        self._seed_initial_data()

    def _seed_initial_data(self):
        sample = WildfireEventResponse(
            id=str(uuid.uuid4()),
            title="Angeles National Forest Heat Signature",
            latitude=34.2439,
            longitude=-118.1753,
            severity="HIGH",
            source="SATELLITE_THERMAL_ALERT",
            description="Initial thermal hotspot detected in canyon ridge.",
            timestamp=datetime.now(timezone.utc),
        )
        self._events.append(sample)

    def get_all_events(self, limit: int = 50) -> List[WildfireEventResponse]:
        """Return list of latest events."""
        return list(reversed(self._events))[:limit]

    def get_event_by_id(self, event_id: str) -> Optional[WildfireEventResponse]:
        """Find an event by its ID."""
        for event in self._events:
            if event.id == event_id:
                return event
        return None

    async def create_event(self, event_in: WildfireEventCreate) -> WildfireEventResponse:
        """Create and store a new event, then broadcast to all connected WebSocket clients."""
        new_event = WildfireEventResponse(
            id=str(uuid.uuid4()),
            title=event_in.title,
            latitude=event_in.latitude,
            longitude=event_in.longitude,
            severity=event_in.severity,
            source=event_in.source,
            description=event_in.description,
            timestamp=datetime.now(timezone.utc),
        )
        self._events.append(new_event)

        # Broadcast realtime notification with standardized envelope
        await manager.broadcast_json({
            "event": "threat.created",
            "type": "WILDFIRE_ALERT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": new_event.model_dump(mode="json"),
        })

        return new_event


# Global singleton instance
event_service = EventService()
