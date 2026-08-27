from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.hotspot import HotspotResponse
from app.db.session import get_db
from app.services.db_service import get_hotspots
from app.auth.security import get_current_user

router = APIRouter(prefix="/hotspots", tags=["Hotspots"])


@router.get("", response_model=List[HotspotResponse], summary="List Thermal Hotspots")
async def list_hotspots(
    min_frp: Optional[float] = Query(default=None, ge=0.0, description="Filter by minimum Fire Radiative Power (MW)"),
    min_confidence: Optional[float] = Query(default=None, ge=0.0, le=100.0, description="Filter by minimum confidence score (%)"),
    limit: int = Query(default=50, ge=1, le=500, description="Max number of hotspots to return"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve list of active thermal hotspot detections with optional filtering."""
    return await get_hotspots(db, min_frp=min_frp, min_confidence=min_confidence, limit=limit)
