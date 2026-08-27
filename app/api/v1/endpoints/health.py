from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.realtime.connection_manager import manager

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
async def get_health():
    """
    Get the health status of the PYRO-SENTRY REST and WebSocket services.
    Returns:
        HealthResponse: status, app name, version, timestamp, and active connection count.
    """
    return HealthResponse(
        status="healthy",
        app_name="PYRO-SENTRY Wildfire Monitoring API",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        active_websocket_connections=manager.connection_count,
    )
