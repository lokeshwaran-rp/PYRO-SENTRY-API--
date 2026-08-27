from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.event import WildfireEventCreate, WildfireEventResponse
from app.services.event_service import event_service

router = APIRouter(prefix="/events", tags=["Events & Alerts"])


@router.get("", response_model=List[WildfireEventResponse], summary="List Wildfire Events")
async def list_events(
    limit: int = Query(default=50, ge=1, le=200, description="Max number of events to retrieve")
):
    """Retrieve list of active or recently reported wildfire events."""
    return event_service.get_all_events(limit=limit)


@router.get("/{event_id}", response_model=WildfireEventResponse, summary="Get Event Details")
async def get_event(event_id: str):
    """Retrieve details for a specific event ID."""
    event = event_service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wildfire event '{event_id}' not found",
        )
    return event


@router.post("", response_model=WildfireEventResponse, status_code=status.HTTP_201_CREATED, summary="Create New Alert")
async def create_event(event_in: WildfireEventCreate):
    """
    Create a new wildfire alert.
    Automatically broadcasts the event to all active WebSocket clients.
    """
    created = await event_service.create_event(event_in)
    return created
