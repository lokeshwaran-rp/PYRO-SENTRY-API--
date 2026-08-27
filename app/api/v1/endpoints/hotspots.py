from typing import List, Optional
from fastapi import APIRouter, Query
from app.schemas.hotspot import HotspotResponse
from app.services.mock_data import get_hotspots

router = APIRouter(prefix="/hotspots", tags=["Hotspots"])


@router.get("", response_model=List[HotspotResponse], summary="List Thermal Hotspots")
async def list_hotspots(
    min_frp: Optional[float] = Query(default=None, ge=0.0, description="Filter by minimum Fire Radiative Power (MW)"),
    min_confidence: Optional[float] = Query(default=None, ge=0.0, le=100.0, description="Filter by minimum confidence score (%)"),
    limit: int = Query(default=50, ge=1, le=500, description="Max number of hotspots to return"),
):
    """Retrieve list of active thermal hotspot detections with optional filtering."""
    return get_hotspots(min_frp=min_frp, min_confidence=min_confidence, limit=limit)
