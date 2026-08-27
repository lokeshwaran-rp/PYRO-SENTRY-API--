from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from app.realtime.publisher import publisher, SUPPORTED_EVENT_TYPES
from app.auth.security import require_role

router = APIRouter(prefix="/realtime", tags=["Realtime WebSocket & Publisher"])


class PublishEventRequest(BaseModel):
    """Payload for publishing a test/demo event to all connected WebSocket clients."""
    event: str = Field(
        ...,
        description="Event type name",
        examples=["hotspot.created"],
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload data dictionary",
        examples=[
            {
                "hotspot_id": "hs-999",
                "latitude": 34.250,
                "longitude": -118.170,
                "frp": 95.4,
                "confidence": 91.0,
            }
        ],
    )


class PublishEventResponse(BaseModel):
    """Response returned after publishing an event."""
    status: str
    message: str
    envelope: Dict[str, Any]
    delivered_to_clients: int


@router.post("/publish", response_model=PublishEventResponse, summary="Publish Event to /ws Subscribers")
async def publish_demo_event(
    req: PublishEventRequest,
    _current_user=Depends(require_role("ADMIN", "OPERATOR")),
):
    """
    Demo / testing endpoint for publishing an event to all connected WebSocket clients on `/ws`.
    Requires ADMIN or OPERATOR role.
    
    **Supported Event Types:**
    - `hotspot.created`
    - `target.updated`
    - `classification.completed`
    - `risk.updated`
    - `threat.created`
    - `threat.updated`
    - `simulation.completed`
    - `system.status`
    """
    if req.event not in SUPPORTED_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported event type '{req.event}'. Must be one of: {sorted(list(SUPPORTED_EVENT_TYPES))}",
        )

    envelope = await publisher.publish(req.event, req.data)
    return PublishEventResponse(
        status="SUCCESS",
        message=f"Event '{req.event}' broadcasted successfully",
        envelope=envelope,
        delivered_to_clients=publisher.manager.connection_count,
    )
