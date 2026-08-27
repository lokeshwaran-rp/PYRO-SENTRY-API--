from .health import router as health_router
from .events import router as events_router
from .simulation import router as simulation_router
from .hotspots import router as hotspots_router
from .targets import router as targets_router
from .threats import router as threats_router
from .analytics import router as analytics_router
from .gis import router as gis_router
from .satellite import router as satellite_router
from .search import router as search_router
from .system import router as system_router
from .realtime import router as realtime_router

__all__ = [
    "health_router",
    "events_router",
    "simulation_router",
    "hotspots_router",
    "targets_router",
    "threats_router",
    "analytics_router",
    "gis_router",
    "satellite_router",
    "search_router",
    "system_router",
    "realtime_router",
]
