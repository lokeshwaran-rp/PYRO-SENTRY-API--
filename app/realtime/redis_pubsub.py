"""
PYRO-SENTRY Redis Pub/Sub Layer.

Replaces the in-process broadcast with Redis-based message distribution.
Background workers/events publish to a Redis channel; each API instance
subscribes and fans out to its locally-connected WebSocket clients.
"""

import json
import asyncio
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection (set during app startup)
_redis_client = None
_subscriber_task: Optional[asyncio.Task] = None


async def init_redis():
    """Initialize the Redis connection. Called on app startup."""
    global _redis_client
    try:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            retry_on_timeout=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )
        # Ping to verify connection
        await _redis_client.ping()
        logger.info(f"Redis connected at {settings.REDIS_URL}")
    except Exception as e:
        logger.warning(f"Redis connection failed ({e}). Falling back to in-process broadcast only.")
        _redis_client = None


async def close_redis():
    """Close the Redis connection. Called on app shutdown."""
    global _redis_client, _subscriber_task
    if _subscriber_task and not _subscriber_task.done():
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed.")
        _redis_client = None


async def publish_to_redis(channel: str, message: dict) -> bool:
    """
    Publish a JSON message to a Redis channel.
    Returns True if published, False if Redis is unavailable.
    """
    if _redis_client is None:
        return False
    try:
        await _redis_client.publish(channel, json.dumps(message, default=str))
        return True
    except Exception as e:
        logger.warning(f"Redis publish failed: {e}")
        return False


async def start_subscriber(channel: str, on_message_callback):
    """
    Start a background task that subscribes to a Redis channel and calls
    the callback for every received message. The callback is typically
    connection_manager.broadcast_json().
    """
    global _subscriber_task
    if _redis_client is None:
        logger.warning("Redis not available — subscriber not started.")
        return

    async def _listen():
        try:
            pubsub = _redis_client.pubsub()
            await pubsub.subscribe(channel)
            logger.info(f"Redis subscriber listening on channel '{channel}'")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await on_message_callback(data)
                    except Exception as e:
                        logger.warning(f"Error processing Redis message: {e}")
        except asyncio.CancelledError:
            logger.info(f"Redis subscriber on '{channel}' cancelled.")
        except Exception as e:
            logger.error(f"Redis subscriber error: {e}", exc_info=True)

    _subscriber_task = asyncio.create_task(_listen())


def get_redis_client():
    """Get the current Redis client (may be None if Redis is unavailable)."""
    return _redis_client


def is_redis_available() -> bool:
    """Check if Redis is connected."""
    return _redis_client is not None
