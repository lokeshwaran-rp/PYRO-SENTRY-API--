"""
Redis Pub/Sub and cross-instance delivery test suite.
Validates:
1. Redis Pub/Sub publishing mechanism.
2. Cross-instance event distribution: Instance A publishes to Redis channel -> Instance B subscriber receives and fans out to its local WebSocket clients.
3. Graceful in-process fallback when Redis is disconnected.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from fakeredis import aioredis as fake_aioredis

from app.realtime.connection_manager import ConnectionManager
from app.realtime.publisher import EventPublisher
from app.realtime.redis_pubsub import publish_to_redis, start_subscriber


@pytest.mark.asyncio
async def test_redis_pubsub_cross_instance_delivery():
    """
    Test cross-instance event delivery:
    Simulates two separate API server instances sharing a Redis broker.
    Instance A publishes an event -> Redis channel -> Instance B's subscriber receives
    and broadcasts to Instance B's local clients.
    """
    # Create shared fake redis server
    fake_server = fake_aioredis.FakeServer()
    redis_instance_a = fake_aioredis.FakeRedis(server=fake_server, decode_responses=True)
    redis_instance_b = fake_aioredis.FakeRedis(server=fake_server, decode_responses=True)

    channel_name = "pyrosentry:test_channel"

    # Instance B: WebSocket ConnectionManager & local subscriber
    manager_b = ConnectionManager()
    mock_ws_client_b = AsyncMock()
    await manager_b.connect(mock_ws_client_b)

    assert manager_b.connection_count == 1

    # Instance B listener loop
    pubsub_b = redis_instance_b.pubsub()
    await pubsub_b.subscribe(channel_name)

    received_events = []

    async def instance_b_listener():
        async for message in pubsub_b.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                received_events.append(data)
                await manager_b.broadcast_json(data)
                break  # Stop after receiving one event for test

    listener_task = asyncio.create_task(instance_b_listener())

    # Wait a moment for subscription to be active
    await asyncio.sleep(0.05)

    # Instance A: Publisher publishing an industrial thermal alert
    test_envelope = {
        "event": "threat.created",
        "timestamp": "2026-08-27T21:40:00Z",
        "data": {
            "threat_id": "threat-test-999",
            "title": "Industrial Flare Anomaly",
            "severity": "HIGH",
        },
    }

    # Instance A publishes to Redis
    await redis_instance_a.publish(channel_name, json.dumps(test_envelope))

    # Wait for Instance B listener to process
    await asyncio.wait_for(listener_task, timeout=2.0)

    # Assertions:
    # 1. Instance B subscriber received the envelope from Redis
    assert len(received_events) == 1
    assert received_events[0]["event"] == "threat.created"
    assert received_events[0]["data"]["threat_id"] == "threat-test-999"

    # 2. Instance B fanned out the envelope to its local WebSocket client
    mock_ws_client_b.send_json.assert_called_once_with(test_envelope)

    # Cleanup
    await pubsub_b.unsubscribe(channel_name)
    await redis_instance_a.close()
    await redis_instance_b.close()


@pytest.mark.asyncio
async def test_publisher_fallback_when_redis_unavailable():
    """Test EventPublisher falls back to direct in-process broadcast when Redis is unavailable."""
    local_manager = ConnectionManager()
    mock_ws = AsyncMock()
    await local_manager.connect(mock_ws)

    # Publisher using local manager and no redis
    publisher_fallback = EventPublisher(connection_manager=local_manager)

    envelope = await publisher_fallback.publish("hotspot.created", {"hotspot_id": "hs-fallback-01"})

    assert envelope["event"] == "hotspot.created"
    assert envelope["data"]["hotspot_id"] == "hs-fallback-01"
    mock_ws.send_json.assert_called_once_with(envelope)
