from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.system import DataSourceStatus, SystemStatusResponse
from app.db.session import get_db
from app.services.db_service import get_data_sources, get_system_status
from app.auth.security import get_current_user

router = APIRouter(prefix="/system", tags=["System & Infrastructure"])


@router.get("/data-sources", response_model=List[DataSourceStatus], summary="Get Data Ingestion Feeds Status")
async def data_sources(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve operational status and ping metrics for external satellite and weather feeds."""
    return await get_data_sources(db)


@router.get("/status", response_model=SystemStatusResponse, summary="Get Platform System Status")
async def system_status(
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve platform pipeline runtime status, module health, memory and CPU metrics."""
    return await get_system_status(db)
