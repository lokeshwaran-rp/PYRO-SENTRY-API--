from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.threat import (
    ThreatResponse,
    ThreatPatchRequest,
    ThreatAcknowledgeRequest,
    ThreatResolveRequest,
)
from app.services.mock_data import (
    get_threats,
    get_threat_by_id,
    patch_threat,
    acknowledge_threat,
    resolve_threat,
)

router = APIRouter(prefix="/threats", tags=["Threats"])


@router.get("", response_model=List[ThreatResponse], summary="List Threats")
async def list_threats(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (OPEN, ACKNOWLEDGED, RESOLVED)"),
    severity: Optional[str] = Query(default=None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(default=50, ge=1, le=200, description="Max threats to return"),
):
    """Retrieve list of identified threats."""
    return get_threats(status=status_filter, severity=severity, limit=limit)


@router.get("/{id}", response_model=ThreatResponse, summary="Get Threat Details")
async def get_threat(id: str):
    """Retrieve a specific threat by ID."""
    threat = get_threat_by_id(id)
    if not threat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threat '{id}' not found",
        )
    return threat


@router.patch("/{id}", response_model=ThreatResponse, summary="Update Threat")
async def update_threat(id: str, patch_data: ThreatPatchRequest):
    """Update fields on a threat (status, severity, notes)."""
    updates = patch_data.model_dump(exclude_unset=True)
    updated = patch_threat(id, updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threat '{id}' not found",
        )
    return updated


@router.post("/{id}/acknowledge", response_model=ThreatResponse, summary="Acknowledge Threat")
async def ack_threat(id: str, request_body: Optional[ThreatAcknowledgeRequest] = None):
    """Acknowledge an active threat."""
    op_name = request_body.operator_name if request_body and request_body.operator_name else "Operator_01"
    updated = acknowledge_threat(id, operator_name=op_name)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threat '{id}' not found",
        )
    return updated


@router.post("/{id}/resolve", response_model=ThreatResponse, summary="Resolve Threat")
async def res_threat(id: str, request_body: Optional[ThreatResolveRequest] = None):
    """Mark a threat as resolved."""
    notes = request_body.resolution_notes if request_body else None
    updated = resolve_threat(id, resolution_notes=notes)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threat '{id}' not found",
        )
    return updated
