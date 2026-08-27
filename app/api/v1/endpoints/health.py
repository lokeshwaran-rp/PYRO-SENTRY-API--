from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.realtime.connection_manager import manager

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
async def get_health():
    """
    Get the health status of the PYRO-SENTRY API services.
    This endpoint is public (no auth required).
    """
    return HealthResponse(
        status="healthy",
        app_name="PYRO-SENTRY Industrial Thermal Surveillance API",
        version="2.0.0",
        timestamp=datetime.now(timezone.utc),
        active_websocket_connections=manager.connection_count,
    )
