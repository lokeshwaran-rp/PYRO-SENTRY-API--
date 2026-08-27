from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ThreatResponse(BaseModel):
    """Schema representing an identified infrastructure or community threat."""
    id: str
    target_id: str
    title: str
    severity: str
    status: str
    risk_score: float
    impact_zone: str
    reported_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None


class ThreatPatchRequest(BaseModel):
    """Schema for updating threat details."""
    severity: Optional[str] = Field(default=None, description="Updated severity (LOW, MEDIUM, HIGH, CRITICAL)")
    status: Optional[str] = Field(default=None, description="Updated status (OPEN, ACKNOWLEDGED, RESOLVED)")
    notes: Optional[str] = Field(default=None, description="Operator notes or operational updates")


class ThreatAcknowledgeRequest(BaseModel):
    """Optional payload for acknowledging a threat."""
    operator_name: Optional[str] = Field(default="Operator_01", description="Name/ID of operator acknowledging threat")


class ThreatResolveRequest(BaseModel):
    """Optional payload for resolving a threat."""
    resolution_notes: Optional[str] = Field(default="Threat mitigated by field crews", description="Mitigation or resolution summary")
