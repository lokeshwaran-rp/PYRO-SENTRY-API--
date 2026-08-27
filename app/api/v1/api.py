from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.simulation import router as simulation_router
from app.api.v1.endpoints.hotspots import router as hotspots_router
from app.api.v1.endpoints.targets import router as targets_router
from app.api.v1.endpoints.threats import router as threats_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.gis import router as gis_router
from app.api.v1.endpoints.satellite import router as satellite_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.system import router as system_router
from app.api.v1.endpoints.realtime import router as realtime_router

api_router = APIRouter()

# Mount all v1 endpoint routers
api_router.include_router(health_router)
api_router.include_router(events_router)
api_router.include_router(simulation_router)
api_router.include_router(hotspots_router)
api_router.include_router(targets_router)
api_router.include_router(threats_router)
api_router.include_router(analytics_router)
api_router.include_router(gis_router)
api_router.include_router(satellite_router)
api_router.include_router(search_router)
api_router.include_router(system_router)
api_router.include_router(realtime_router)
