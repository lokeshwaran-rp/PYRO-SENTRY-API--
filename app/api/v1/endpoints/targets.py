from typing import List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.target import (
    TargetDetail, TargetObservation, TargetHistoryItem,
    TargetClassification, TargetRisk, TargetEvidence, TargetSatellite,
)
from app.db.session import get_db
from app.services.db_service import get_targets, get_target_by_id, get_target_subresource
from app.auth.security import get_current_user

router = APIRouter(prefix="/targets", tags=["Targets"])


@router.get("", summary="List Surveillance Targets")
async def list_targets(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (e.g. ACTIVE, MONITORING)"),
    threat_level: Optional[str] = Query(default=None, description="Filter by threat level (e.g. HIGH, MEDIUM, LOW)"),
    limit: int = Query(default=50, ge=1, le=200, description="Max number of targets to return"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve list of identified thermal anomaly targets / hotspot clusters."""
    return await get_targets(db, status=status_filter, threat_level=threat_level, limit=limit)


@router.get("/{id}", summary="Get Target Details")
async def get_target(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve complete details for a specific target ID."""
    target = await get_target_by_id(db, id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{id}' not found")
    return target


@router.get("/{id}/observations", summary="Get Target Observations")
async def get_target_observations(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve observation history and sensor passes for a target."""
    data = await get_target_subresource(db, id, "observations")
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observations for target '{id}' not found")
    return data


@router.get("/{id}/history", summary="Get Target History")
async def get_target_history(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve lifecycle events and state audit log for a target."""
    data = await get_target_subresource(db, id, "history")
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"History for target '{id}' not found")
    return data


@router.get("/{id}/classification", summary="Get Target Classification")
async def get_target_classification(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve classifier predictions and class probabilities for a target."""
    data = await get_target_subresource(db, id, "classification")
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Classification for target '{id}' not found")
    return data


@router.get("/{id}/risk", summary="Get Target Risk Assessment")
async def get_target_risk(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve risk score, threatened assets, and spread rate for a target."""
    data = await get_target_subresource(db, id, "risk")
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Risk assessment for target '{id}' not found")
    return data


@router.get("/{id}/evidence", summary="Get Target Evidence")
async def get_target_evidence(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve multi-source sensor and environmental evidence for a target."""
    data = await get_target_subresource(db, id, "evidence")
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence for target '{id}' not found")
    return data


@router.get("/{id}/satellite", summary="Get Target Satellite Data")
async def get_target_satellite(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve satellite pass metadata and imagery details for a target."""
    data = await get_target_subresource(db, id, "satellite")
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Satellite pass data for target '{id}' not found")
    return data
