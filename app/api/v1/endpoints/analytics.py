from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.analytics import AnalyticsSummaryResponse, FRPTrendPoint, HourlyActivityPoint
from app.db.session import get_db
from app.services.db_service import (
    get_analytics_summary, get_frp_trends,
    get_classification_distribution, get_hourly_activity,
)
from app.auth.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse, summary="Get Analytics Summary")
async def analytics_summary(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve high-level dashboard metrics and active detection stats."""
    return await get_analytics_summary(db)


@router.get("/frp-trends", response_model=List[FRPTrendPoint], summary="Get FRP Trends")
async def frp_trends(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve Fire Radiative Power (MW) time-series trend data."""
    return await get_frp_trends(db)


@router.get("/classification-distribution", response_model=Dict[str, int], summary="Get Classification Breakdown")
async def classification_distribution(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve distribution count of detection classifications."""
    return await get_classification_distribution(db)


@router.get("/hourly-activity", response_model=List[HourlyActivityPoint], summary="Get Hourly Activity Breakdown")
async def hourly_activity(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve hourly detection frequency for diurnal activity tracking."""
    return await get_hourly_activity(db)
