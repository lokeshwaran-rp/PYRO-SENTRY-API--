from typing import List, Dict
from fastapi import APIRouter
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    FRPTrendPoint,
    HourlyActivityPoint,
)
from app.services.mock_data import (
    MOCK_ANALYTICS_SUMMARY,
    MOCK_FRP_TRENDS,
    MOCK_CLASSIFICATION_DISTRIBUTION,
    MOCK_HOURLY_ACTIVITY,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse, summary="Get Analytics Summary")
async def get_analytics_summary():
    """Retrieve high-level dashboard metrics and active fire stats."""
    return MOCK_ANALYTICS_SUMMARY


@router.get("/frp-trends", response_model=List[FRPTrendPoint], summary="Get FRP Trends")
async def get_frp_trends():
    """Retrieve Fire Radiative Power (MW) time-series trend data."""
    return MOCK_FRP_TRENDS


@router.get("/classification-distribution", response_model=Dict[str, int], summary="Get Classification Breakdown")
async def get_classification_distribution():
    """Retrieve distribution count of detection classifications (Wildfire, Prescribed, Flare, etc.)."""
    return MOCK_CLASSIFICATION_DISTRIBUTION


@router.get("/hourly-activity", response_model=List[HourlyActivityPoint], summary="Get Hourly Activity Breakdown")
async def get_hourly_activity():
    """Retrieve hourly detection frequency for diurnal activity tracking."""
    return MOCK_HOURLY_ACTIVITY
