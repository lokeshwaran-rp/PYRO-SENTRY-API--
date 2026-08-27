from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HotspotResponse(BaseModel):
    """Schema representing a thermal hotspot detection."""
    id: str = Field(..., description="Unique hotspot identifier")
    latitude: float = Field(..., description="Hotspot latitude")
    longitude: float = Field(..., description="Hotspot longitude")
    frp: float = Field(..., description="Fire Radiative Power (MW)")
    confidence: float = Field(..., description="Detection confidence percentage (0-100)")
    satellite: str = Field(..., description="Satellite sensor name")
    detected_at: datetime = Field(..., description="Timestamp of sensor detection")
    target_id: Optional[str] = Field(default=None, description="Associated target cluster ID")
