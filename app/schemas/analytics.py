from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field


class AnalyticsSummaryResponse(BaseModel):
    """Overall dashboard analytics summary counters."""
    active_targets_count: int
    total_hotspots_detected_24h: int
    critical_threats_count: int
    total_estimated_burned_ha: float
    average_confidence_pct: float
    highest_frp_mw: float
    last_updated: datetime


class FRPTrendPoint(BaseModel):
    """Data point for FRP time-series chart."""
    timestamp: datetime
    total_frp_mw: float
    hotspots_count: int


class HourlyActivityPoint(BaseModel):
    """Hourly detection frequency data point."""
    hour_utc: str
    detections: int
