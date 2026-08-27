import logging
from datetime import datetime, timezone
from typing import Dict, Any
from .connection_manager import manager
from .redis_pubsub import publish_to_redis, is_redis_available
from app.core.config import settings

logger = logging.getLogger(__name__)

# Supported standardized event types
SUPPORTED_EVENT_TYPES = {
    "hotspot.created",
    "target.updated",
    "classification.completed",
    "risk.updated",
    "threat.created",
    "threat.updated",
    "simulation.completed",
    "system.status",
}


class EventPublisher:
    """
    Event Publisher for PYRO-SENTRY realtime streams.

    When Redis is available, publishes to Redis channel (for cross-instance delivery).
    When Redis is unavailable, falls back to direct in-process broadcast.
    """

    def __init__(self, connection_manager=manager):
        self.manager = connection_manager

    async def publish(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a standardized event envelope.

        If Redis is connected: publishes to Redis channel → subscriber picks up → broadcasts to local WS clients.
        If Redis is NOT connected: falls back to direct in-process broadcast.
        """
        envelope = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        # Try Redis first (for cross-instance delivery)
        published_to_redis = await publish_to_redis(settings.REDIS_CHANNEL, envelope)

        if not published_to_redis:
            # Fallback: direct in-process broadcast
            await self.manager.broadcast_json(envelope)
            logger.info(f"Published event '{event_type}' via in-process broadcast to {self.manager.connection_count} clients.")
        else:
            logger.info(f"Published event '{event_type}' via Redis channel '{settings.REDIS_CHANNEL}'.")

        return envelope

    # --- Convenience Helper Methods ---

    async def publish_hotspot_created(self, hotspot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish hotspot.created event."""
        return await self.publish("hotspot.created", hotspot_data)

    async def publish_target_updated(self, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish target.updated event."""
        return await self.publish("target.updated", target_data)

    async def publish_classification_completed(self, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish classification.completed event."""
        return await self.publish("classification.completed", classification_data)

    async def publish_risk_updated(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish risk.updated event."""
        return await self.publish("risk.updated", risk_data)

    async def publish_threat_created(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish threat.created event."""
        return await self.publish("threat.created", threat_data)

    async def publish_threat_updated(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish threat.updated event."""
        return await self.publish("threat.updated", threat_data)

    async def publish_simulation_completed(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish simulation.completed event."""
        return await self.publish("simulation.completed", simulation_data)

    async def publish_system_status(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish system.status event."""
        return await self.publish("system.status", status_data)


# Global singleton instance for publishing events across the app
publisher = EventPublisher()
