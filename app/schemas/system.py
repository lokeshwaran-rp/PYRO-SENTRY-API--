from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class DataSourceStatus(BaseModel):
    """Status information for an external ingestion feed."""
    name: str
    type: str
    status: str
    last_sync: datetime
    ping_ms: int
    items_ingested_last_hour: int


class SystemStatusResponse(BaseModel):
    """System runtime and pipeline health status."""
    system_name: str
    version: str
    status: str
    uptime_seconds: int
    pipeline_latency_ms: int
    active_modules: List[str]
    memory_usage_mb: float
    cpu_load_pct: float
