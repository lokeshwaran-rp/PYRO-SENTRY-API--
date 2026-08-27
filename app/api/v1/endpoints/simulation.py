from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from app.schemas.simulation import (
    SimulationStartRequest, SimulationStatusResponse,
    SimulationStopResponse, SimulationRunRequest, SimulationRunResponse,
    SimulationEvidenceItem, SimulationSmokeEstimate, SimulationImpactEstimate,
)
from app.services.simulation_service import simulation_service
from app.intelligence.classifier import classify
from app.intelligence.risk import compute_risk
from app.auth.security import get_current_user, require_role

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post(
    "/run",
    response_model=SimulationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Stateless Simulation Inference",
)
async def run_simulation_inference(
    request: SimulationRunRequest,
    _current_user=Depends(require_role("ADMIN", "OPERATOR", "ANALYST")),
):
    """
    Run an isolated, stateless classification + risk simulation using the REAL intelligence pipeline.

    This endpoint calls the exact same classifier and risk scorer used by the live pipeline,
    guaranteeing no divergence between simulated and real results.

    **Guaranteed non-destructive**: Does NOT modify any existing targets, observations, or threats.
    """
    # Call the REAL classifier (single source of truth)
    classification = classify(
        frp=request.frp,
        brightness=request.brightness,
        persistence=request.persistence,
        industrial_proximity=request.industrial_proximity,
        wind_speed=request.wind_speed,
        wind_direction=request.wind_direction,
        ndvi=request.ndvi,
        nbr=request.nbr,
        swir_anomaly=request.swir_anomaly,
    )

    # Call the REAL risk scorer (single source of truth)
    risk = compute_risk(
        frp=request.frp,
        brightness=request.brightness,
        persistence=request.persistence,
        industrial_proximity=request.industrial_proximity,
        wind_speed=request.wind_speed,
        wind_direction=request.wind_direction,
        ndvi=request.ndvi,
        nbr=request.nbr,
        swir_anomaly=request.swir_anomaly,
        classification=classification,
    )

    # Convert evidence to schema format
    evidence_items = [
        SimulationEvidenceItem(
            factor=e.factor, value=e.value, impact=e.impact, weight=e.weight
        )
        for e in classification.evidence
    ]

    smoke_est = SimulationSmokeEstimate(
        plume_height_m=risk.smoke_estimate.plume_height_m,
        dispersion_direction=risk.smoke_estimate.dispersion_direction,
        pm25_threat_level=risk.smoke_estimate.pm25_threat_level,
        affected_radius_km=risk.smoke_estimate.affected_radius_km,
    )

    impact_est = SimulationImpactEstimate(
        estimated_burned_ha_24h=risk.impact_estimate.estimated_burned_ha_24h,
        containment_difficulty=risk.impact_estimate.containment_difficulty,
        threatened_infrastructure_radius_km=risk.impact_estimate.threatened_infrastructure_radius_km,
    )

    return SimulationRunResponse(
        is_simulated=True,
        simulation_mode="SIMULATED",
        simulation_timestamp=datetime.now(timezone.utc),
        status="COMPLETED",
        classification=classification.primary_class,
        confidence=classification.confidence,
        risk_score=risk.risk_score,
        risk_level=risk.risk_level,
        evidence=evidence_items,
        smoke_estimate=smoke_est,
        impact_estimate=impact_est,
    )


@router.get("/status", response_model=SimulationStatusResponse, summary="Get Simulation Status")
async def get_simulation_status(_current_user=Depends(get_current_user)):
    """Check whether a spatial spread simulation is running and retrieve the latest step data."""
    return simulation_service.get_status()


@router.post(
    "/start",
    response_model=SimulationStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start Spatial Spread Simulation",
)
async def start_simulation(
    request: SimulationStartRequest = SimulationStartRequest(),
    _current_user=Depends(require_role("ADMIN", "OPERATOR")),
):
    """Start a background thermal spread simulation with realtime WebSocket streaming."""
    return await simulation_service.start_simulation(request)


@router.post("/stop", response_model=SimulationStopResponse, summary="Stop Spatial Spread Simulation")
async def stop_simulation(_current_user=Depends(require_role("ADMIN", "OPERATOR"))):
    """Stop the currently running spatial spread simulation."""
    return await simulation_service.stop_simulation()
