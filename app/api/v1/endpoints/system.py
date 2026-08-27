from typing import List
from fastapi import APIRouter
from app.schemas.system import DataSourceStatus, SystemStatusResponse
from app.services.mock_data import MOCK_DATA_SOURCES, MOCK_SYSTEM_STATUS

router = APIRouter(prefix="/system", tags=["System & Infrastructure"])


@router.get("/data-sources", response_model=List[DataSourceStatus], summary="Get Data Ingestion Feeds Status")
async def get_data_sources():
    """Retrieve operational status and ping metrics for external satellite and weather feeds."""
    return MOCK_DATA_SOURCES


@router.get("/status", response_model=SystemStatusResponse, summary="Get Platform System Status")
async def get_system_status():
    """Retrieve platform pipeline runtime status, module health, memory and CPU metrics."""
    return MOCK_SYSTEM_STATUS
