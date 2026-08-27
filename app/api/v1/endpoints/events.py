from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.schemas.event import WildfireEventCreate, WildfireEventResponse
from app.db.session import get_db
from app.services.db_service import get_all_events, get_event_by_id, create_event
from app.realtime.publisher import publisher
from app.auth.security import get_current_user, require_role

router = APIRouter(prefix="/events", tags=["Events & Alerts"])


@router.get("", response_model=List[WildfireEventResponse], summary="List Alert Events")
async def list_events(
    limit: int = Query(default=50, ge=1, le=200, description="Max number of events to retrieve"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve list of active or recently reported alert events."""
    return await get_all_events(db, limit=limit)


@router.get("/{event_id}", response_model=WildfireEventResponse, summary="Get Event Details")
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve details for a specific event ID."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event '{event_id}' not found")
    return event


@router.post("", response_model=WildfireEventResponse, status_code=status.HTTP_201_CREATED, summary="Create New Alert")
async def create_new_event(
    event_in: WildfireEventCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("ADMIN", "OPERATOR")),
):
    """Create a new alert event. Broadcasts to all connected WebSocket clients."""
    event_data = event_in.model_dump()
    created = await create_event(db, event_data)

    # Broadcast via Redis/WS
    await publisher.publish("threat.created", created)

    return created
