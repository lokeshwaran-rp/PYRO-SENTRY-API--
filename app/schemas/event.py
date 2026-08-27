from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WildfireEventCreate(BaseModel):
    """Schema for creating/reporting a new wildfire event alert."""
    title: str = Field(..., examples=["North Ridge Fire Detection"], description="Brief summary of event")
    latitude: float = Field(..., ge=-90.0, le=90.0, examples=[37.7749], description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, examples=[-122.4194], description="Longitude coordinate")
    severity: str = Field(default="MEDIUM", examples=["HIGH"], description="Severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    source: str = Field(default="MANUAL_REPORT", examples=["SENSOR_STATION_04"], description="Origin/Source of the report")
    description: Optional[str] = Field(default=None, description="Detailed notes on the incident")


class WildfireEventResponse(WildfireEventCreate):
    """Schema for returning wildfire event data."""
    id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Creation/Detection timestamp")
