from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(default="healthy", description="Current service health status")
    app_name: str = Field(default="PYRO-SENTRY API", description="Name of the application")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Server UTC timestamp",
    )
    active_websocket_connections: int = Field(default=0, description="Count of connected clients")
