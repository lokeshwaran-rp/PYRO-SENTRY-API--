from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.target import (
    TargetDetail,
    TargetObservation,
    TargetHistoryItem,
    TargetClassification,
    TargetRisk,
    TargetEvidence,
    TargetSatellite,
)
from app.services.mock_data import (
    get_targets,
    get_target_by_id,
    get_target_subresource,
)

router = APIRouter(prefix="/targets", tags=["Targets"])


@router.get("", response_model=List[TargetDetail], summary="List Wildfire Targets")
async def list_targets(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (e.g. ACTIVE, MONITORING)"),
    threat_level: Optional[str] = Query(default=None, description="Filter by threat level (e.g. HIGH, MEDIUM, LOW)"),
    limit: int = Query(default=50, ge=1, le=200, description="Max number of targets to return"),
):
    """Retrieve list of identified wildfire targets / hotspot clusters."""
    return get_targets(status=status_filter, threat_level=threat_level, limit=limit)


@router.get("/{id}", response_model=TargetDetail, summary="Get Target Details")
async def get_target(id: str):
    """Retrieve complete details for a specific target ID."""
    target = get_target_by_id(id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target '{id}' not found",
        )
    return target


@router.get("/{id}/observations", response_model=List[TargetObservation], summary="Get Target Observations")
async def get_target_observations(id: str):
    """Retrieve observation history and sensor passes for a target."""
    data = get_target_subresource(id, "observations")
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observations for target '{id}' not found",
        )
    return data


@router.get("/{id}/history", response_model=List[TargetHistoryItem], summary="Get Target History")
async def get_target_history(id: str):
    """Retrieve lifecycle events and state audit log for a target."""
    data = get_target_subresource(id, "history")
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History for target '{id}' not found",
        )
    return data


@router.get("/{id}/classification", response_model=TargetClassification, summary="Get Target Classification")
async def get_target_classification(id: str):
    """Retrieve classifier predictions and class probabilities for a target."""
    data = get_target_subresource(id, "classification")
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classification for target '{id}' not found",
        )
    return data


@router.get("/{id}/risk", response_model=TargetRisk, summary="Get Target Risk Assessment")
async def get_target_risk(id: str):
    """Retrieve risk score, threatened assets, and spread rate for a target."""
    data = get_target_subresource(id, "risk")
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk assessment for target '{id}' not found",
        )
    return data


@router.get("/{id}/evidence", response_model=TargetEvidence, summary="Get Target Evidence")
async def get_target_evidence(id: str):
    """Retrieve multi-source sensor and environmental evidence for a target."""
    data = get_target_subresource(id, "evidence")
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence for target '{id}' not found",
        )
    return data


@router.get("/{id}/satellite", response_model=TargetSatellite, summary="Get Target Satellite Data")
async def get_target_satellite(id: str):
    """Retrieve satellite pass metadata and imagery details for a target."""
    data = get_target_subresource(id, "satellite")
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Satellite pass data for target '{id}' not found",
        )
    return data
