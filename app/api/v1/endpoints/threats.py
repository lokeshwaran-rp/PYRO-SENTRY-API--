from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.threat import (
    ThreatResponse, ThreatPatchRequest, ThreatAcknowledgeRequest, ThreatResolveRequest,
)
from app.db.session import get_db
from app.services.db_service import (
    get_threats, get_threat_by_id, patch_threat, acknowledge_threat, resolve_threat,
)
from app.auth.security import get_current_user, require_role

router = APIRouter(prefix="/threats", tags=["Threats"])


@router.get("", response_model=List[ThreatResponse], summary="List Threats")
async def list_threats(
    status_filter: Optional[str] = Query(default=None, alias="status",
        description="Filter by status (NEW, ACKNOWLEDGED, INVESTIGATING, DISPATCHED, RESOLVED, FALSE_POSITIVE)"),
    severity: Optional[str] = Query(default=None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(default=50, ge=1, le=200, description="Max threats to return"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve list of identified threats."""
    return await get_threats(db, status=status_filter, severity=severity, limit=limit)


@router.get("/{id}", response_model=ThreatResponse, summary="Get Threat Details")
async def get_threat(
    id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve a specific threat by ID."""
    threat = await get_threat_by_id(db, id)
    if not threat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Threat '{id}' not found")
    return threat


@router.patch("/{id}", response_model=ThreatResponse, summary="Update Threat")
async def update_threat(
    id: str,
    patch_data: ThreatPatchRequest,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("ADMIN", "OPERATOR")),
):
    """Update fields on a threat (status, severity, notes). Enforces lifecycle transition rules."""
    updates = patch_data.model_dump(exclude_unset=True)
    try:
        updated = await patch_threat(db, id, updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Threat '{id}' not found")
    return updated


@router.post("/{id}/acknowledge", response_model=ThreatResponse, summary="Acknowledge Threat")
async def ack_threat(
    id: str,
    request_body: Optional[ThreatAcknowledgeRequest] = None,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("ADMIN", "OPERATOR")),
):
    """Acknowledge a threat. Validates lifecycle transition (must be in NEW state)."""
    op_name = request_body.operator_name if request_body and request_body.operator_name else "Operator_01"
    try:
        updated = await acknowledge_threat(db, id, operator_name=op_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Threat '{id}' not found")
    return updated


@router.post("/{id}/resolve", response_model=ThreatResponse, summary="Resolve Threat")
async def res_threat(
    id: str,
    request_body: Optional[ThreatResolveRequest] = None,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("ADMIN", "OPERATOR")),
):
    """Resolve a threat. Validates lifecycle transition (must be in DISPATCHED state)."""
    notes = request_body.resolution_notes if request_body else None
    try:
        updated = await resolve_threat(db, id, resolution_notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Threat '{id}' not found")
    return updated
