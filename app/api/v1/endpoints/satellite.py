from fastapi import APIRouter, HTTPException, status
from app.schemas.satellite import SatelliteEvidenceResponse
from app.services.mock_data import get_satellite_evidence

router = APIRouter(prefix="/satellite", tags=["Satellite Evidence"])


@router.get("/evidence/{target_id}", response_model=SatelliteEvidenceResponse, summary="Get Target Satellite Evidence")
async def get_target_satellite_evidence(target_id: str):
    """Retrieve detailed high-resolution satellite imagery evidence and SWIR anomalies for a target."""
    data = get_satellite_evidence(target_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Satellite evidence for target '{target_id}' not found",
        )
    return data
