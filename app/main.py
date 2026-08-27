"""
PYRO-SENTRY Industrial Thermal Surveillance API.

Main FastAPI application entrypoint providing REST endpoints, WebSocket streams,
realtime Redis pub/sub distribution, JWT authentication, and intelligence simulation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.auth.router import router as auth_router
from app.api.v1.api import api_router
from app.realtime.websocket_router import router as websocket_router
from app.realtime.connection_manager import manager
from app.realtime.redis_pubsub import init_redis, close_redis, start_subscriber
from app.db.session import engine
from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import AsyncSessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown hooks."""
    # 1. Initialize Database Tables and Seeds (if development/standalone)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_database(session)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Database auto-migration/seed skipped or failed: {e}")

    # 2. Initialize Redis Pub/Sub
    await init_redis()
    await start_subscriber(settings.REDIS_CHANNEL, manager.broadcast_json)

    yield

    # 3. Shutdown: Close Redis
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="PYRO-SENTRY Industrial Thermal Surveillance API",
    description="""
    ## PYRO-SENTRY Industrial Thermal Surveillance API Backend
    
    Central API and Realtime Communication Hub:
    * **Authentication (`/auth`)**: JWT register, login, refresh, profile (`/auth/me`), logout, and RBAC.
    * **Thermal Surveillance (`/api/v1`)**: Hotspot detections, targets, threat lifecycle management, GIS layers, satellite evidence, system metrics.
    * **Simulation Engine (`/api/v1/simulation`)**: Evidence-first inference powered directly by the real intelligence classifier and risk pipeline.
    * **Realtime Gateway (`/ws`)**: Redis Pub/Sub-backed WebSocket broadcast engine for multi-instance scaling.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Auth router
app.include_router(auth_router)

# Mount REST API routers
app.include_router(api_router, prefix="/api/v1")

# Mount Realtime WebSocket router
app.include_router(websocket_router)


@app.get("/", tags=["Root"])
async def root():
    """Root landing endpoint."""
    return {
        "message": "Welcome to PYRO-SENTRY Industrial Thermal Surveillance API",
        "docs": "/docs",
        "health": "/api/v1/health",
        "websocket": "/ws/realtime",
        "auth": "/auth/login",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
