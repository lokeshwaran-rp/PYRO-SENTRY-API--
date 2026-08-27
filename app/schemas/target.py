from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class TargetObservation(BaseModel):
    """Observation item recorded for a target."""
    observation_id: str
    timestamp: datetime
    sensor: str
    frp: float
    brightness_temp_k: float
    confidence: float


class TargetHistoryItem(BaseModel):
    """Audit log / history item for a target."""
    event: str
    timestamp: datetime
    details: str


class TargetClassification(BaseModel):
    """Classification details for a target."""
    target_id: str
    primary_class: str
    confidence: float
    probabilities: Dict[str, float]
    model_version: str
    evaluated_at: datetime


class TargetRisk(BaseModel):
    """Risk assessment for a target."""
    target_id: str
    risk_score: float
    risk_category: str
    proximity_to_assets_km: float
    threatened_assets: List[str]
    wind_speed_kmh: float
    wind_direction: str
    rate_of_spread_m_min: float


class EvidenceItem(BaseModel):
    """Single evidence point supporting the detection."""
    type: str
    sensor: Optional[str] = None
    source: Optional[str] = None
    value: str
    weight: float


class TargetEvidence(BaseModel):
    """Aggregated evidence for a target."""
    target_id: str
    evidence_count: int
    items: List[EvidenceItem]


class TargetSatellite(BaseModel):
    """Satellite pass information and imagery metadata for target."""
    target_id: str
    satellite: str
    pass_time: datetime
    cloud_cover_pct: float
    bands_available: List[str]
    image_url: str
    ground_resolution_m: float


class TargetDetail(BaseModel):
    """Full detail model for a wildfire target."""
    id: str
    name: str
    status: str
    latitude: float
    longitude: float
    estimated_area_ha: float
    max_frp: float
    confidence_score: float
    first_detected: datetime
    last_updated: datetime
    threat_level: str
    observations: Optional[List[TargetObservation]] = None
    history: Optional[List[TargetHistoryItem]] = None
    classification: Optional[TargetClassification] = None
    risk: Optional[TargetRisk] = None
    evidence: Optional[TargetEvidence] = None
    satellite: Optional[TargetSatellite] = None
