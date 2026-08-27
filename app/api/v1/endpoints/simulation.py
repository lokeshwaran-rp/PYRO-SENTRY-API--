from fastapi import APIRouter, status
from app.schemas.simulation import (
    SimulationStartRequest,
    SimulationStatusResponse,
    SimulationStopResponse,
    SimulationRunRequest,
    SimulationRunResponse,
)
from app.services.simulation_service import simulation_service
from app.simulation.engine import SimulationEngine

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post(
    "/run",
    response_model=SimulationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Stateless Simulation Inference",
)
async def run_simulation_inference(request: SimulationRunRequest):
    """
    Run an isolated, stateless wildfire simulation calculation based on input features.
    
    **Inputs:**
    - `frp`: Fire Radiative Power in MW
    - `brightness`: Brightness temperature in Kelvin
    - `persistence`: Consecutive detection passes
    - `industrial_proximity`: Distance in km to nearest industrial asset
    - `wind_speed`: Wind speed in km/h
    - `wind_direction`: Wind azimuth (0 - 360 degrees)
    - `ndvi`: Normalized Difference Vegetation Index (-1.0 to 1.0)
    - `nbr`: Normalized Burn Ratio (-1.0 to 1.0)
    - `swir_anomaly`: Short-Wave Infrared anomaly index
    
    **Output:**
    - Returns simulated classification, confidence, risk score/level, evidence, smoke estimate, and impact estimate.
    - Explicitly marked with `is_simulated: true`.
    - **Guaranteed non-destructive**: Does NOT modify any existing targets, observations, or threats.
    """
    return SimulationEngine.evaluate_simulation_run(request)


@router.get("/status", response_model=SimulationStatusResponse, summary="Get Simulation Status")
async def get_simulation_status():
    """Check whether a fire spread simulation is running and retrieve the latest step data."""
    return simulation_service.get_status()


@router.post(
    "/start",
    response_model=SimulationStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start Fire Spread Simulation",
)
async def start_simulation(request: SimulationStartRequest = SimulationStartRequest()):
    """
    Start a mock wildfire spread simulation.
    
    The simulation will run asynchronously in the background, periodically computing
    perimeter spread steps and streaming them in realtime to all WebSocket clients.
    """
    return await simulation_service.start_simulation(request)


@router.post("/stop", response_model=SimulationStopResponse, summary="Stop Fire Spread Simulation")
async def stop_simulation():
    """Stop the currently running wildfire spread simulation."""
    return await simulation_service.stop_simulation()
