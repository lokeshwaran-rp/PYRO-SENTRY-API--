from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.satellite import SatelliteEvidenceResponse
from app.db.session import get_db
from app.services.db_service import get_satellite_evidence
from app.auth.security import get_current_user

router = APIRouter(prefix="/satellite", tags=["Satellite Evidence"])


@router.get("/evidence/{target_id}", response_model=SatelliteEvidenceResponse, summary="Get Target Satellite Evidence")
async def get_target_satellite_evidence(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve detailed satellite imagery evidence and SWIR anomalies for a target."""
    data = await get_satellite_evidence(db, target_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Satellite evidence for target '{target_id}' not found")
    return data
