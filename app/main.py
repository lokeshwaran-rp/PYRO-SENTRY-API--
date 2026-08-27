from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.realtime.websocket_router import router as websocket_router

app = FastAPI(
    title="PYRO-SENTRY Wildfire Monitoring API",
    description="""
    ## PYRO-SENTRY Backend API (Lokesh's Role)
    
    This service provides:
    * **REST APIs**: Health checks (`/api/v1/health`), event retrieval & reporting (`/api/v1/events`).
    * **WebSocket Realtime**: Live streaming of alerts and fire spread steps (`/ws/realtime`).
    * **Simulation API**: Control and stream wildfire spread simulations (`/api/v1/simulation`).
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API routers
app.include_router(api_router, prefix="/api/v1")

# Mount Realtime WebSocket router
app.include_router(websocket_router)


@app.get("/", tags=["Root"])
async def root():
    """Root landing endpoint."""
    return {
        "message": "Welcome to PYRO-SENTRY Wildfire Monitoring API",
        "docs": "/docs",
        "health": "/api/v1/health",
        "websocket": "/ws/realtime",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
