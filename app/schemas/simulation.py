from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class SimulationStartRequest(BaseModel):
    """Schema for initiating a wildfire spread simulation."""
    simulation_id: Optional[str] = Field(default=None, description="Optional custom ID for the simulation run")
    latitude: float = Field(default=34.0522, ge=-90.0, le=90.0, description="Center latitude of ignition")
    longitude: float = Field(default=-118.2437, ge=-180.0, le=180.0, description="Center longitude of ignition")
    wind_speed_kmh: float = Field(default=15.0, ge=0.0, description="Wind speed in km/h")
    wind_direction_deg: float = Field(default=45.0, ge=0.0, le=360.0, description="Wind direction in degrees (0-360)")
    max_steps: int = Field(default=20, ge=1, le=100, description="Maximum number of simulation steps to run")
    step_interval_seconds: float = Field(default=1.0, ge=0.2, le=10.0, description="Interval in seconds between steps")


class SimulationStepData(BaseModel):
    """Schema representing a single step in the fire spread simulation."""
    simulation_id: str
    step_number: int
    timestamp: datetime
    burned_area_hectares: float
    front_coordinates: List[List[float]] = Field(
        ..., description="List of [latitude, longitude] perimeter points"
    )
    containment_pct: float


class SimulationStatusResponse(BaseModel):
    """Schema for reporting the status of the simulation service."""
    is_running: bool
    current_simulation_id: Optional[str] = None
    step_count: int = 0
    max_steps: int = 0
    started_at: Optional[datetime] = None
    latest_step: Optional[SimulationStepData] = None


class SimulationStopResponse(BaseModel):
    """Schema for stopping a simulation."""
    message: str
    simulation_id: Optional[str]
    steps_completed: int


# --- Schemas for POST /api/v1/simulation/run ---

class SimulationRunRequest(BaseModel):
    """Input features for running a stateless simulation calculation."""
    frp: float = Field(
        ...,
        ge=0.0,
        description="Fire Radiative Power in MW",
        examples=[115.4],
    )
    brightness: float = Field(
        ...,
        ge=200.0,
        le=550.0,
        description="Brightness temperature in Kelvin",
        examples=[382.5],
    )
    persistence: int = Field(
        default=1,
        ge=1,
        description="Consecutive sensor detection count",
        examples=[3],
    )
    industrial_proximity: float = Field(
        ...,
        ge=0.0,
        description="Distance in km to nearest known industrial facility",
        examples=[4.2],
    )
    wind_speed: float = Field(
        ...,
        ge=0.0,
        description="Wind speed in km/h",
        examples=[24.5],
    )
    wind_direction: float = Field(
        ...,
        ge=0.0,
        le=360.0,
        description="Wind direction in degrees (0-360 azimuth)",
        examples=[55.0],
    )
    ndvi: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Normalized Difference Vegetation Index (-1.0 to 1.0)",
        examples=[0.15],
    )
    nbr: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Normalized Burn Ratio (-1.0 to 1.0)",
        examples=[-0.25],
    )
    swir_anomaly: float = Field(
        ...,
        ge=0.0,
        description="Short-Wave Infrared anomaly index",
        examples=[3.8],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "frp": 115.4,
                    "brightness": 382.5,
                    "persistence": 3,
                    "industrial_proximity": 4.2,
                    "wind_speed": 24.5,
                    "wind_direction": 55.0,
                    "ndvi": 0.15,
                    "nbr": -0.25,
                    "swir_anomaly": 3.8,
                }
            ]
        }
    }


class SimulationEvidenceItem(BaseModel):
    """Evidence item supporting the simulated inference."""
    factor: str
    value: str
    impact: str
    weight: float


class SimulationSmokeEstimate(BaseModel):
    """Simulated smoke dispersion and plume metrics."""
    plume_height_m: float
    dispersion_direction: float
    pm25_threat_level: str
    affected_radius_km: float


class SimulationImpactEstimate(BaseModel):
    """Simulated impact assessment."""
    estimated_burned_ha_24h: float
    containment_difficulty: str
    threatened_infrastructure_radius_km: float


class SimulationRunResponse(BaseModel):
    """Simulated inference output."""
    is_simulated: bool = Field(default=True, description="Explicit indicator that this is a synthetic simulation output")
    simulation_mode: str = Field(default="SIMULATED", description="Mode identifier")
    simulation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Simulation run timestamp",
    )
    status: str = Field(default="COMPLETED", description="Simulation status")
    classification: str = Field(..., description="Simulated classification (WILDFIRE, INDUSTRIAL_FLARE, PRESCRIBED_BURN, FALSE_POSITIVE)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Simulated classification confidence (0.0 - 1.0)")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Calculated composite risk score (0.0 - 10.0)")
    risk_level: str = Field(..., description="Risk tier: LOW, MODERATE, HIGH, CRITICAL")
    evidence: List[SimulationEvidenceItem] = Field(..., description="Simulated evidence breakdown")
    smoke_estimate: SimulationSmokeEstimate = Field(..., description="Simulated smoke dispersion estimate")
    impact_estimate: SimulationImpactEstimate = Field(..., description="Simulated impact estimate")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_simulated": True,
                    "simulation_mode": "SIMULATED",
                    "simulation_timestamp": "2026-08-26T21:40:00Z",
                    "status": "COMPLETED",
                    "classification": "WILDFIRE",
                    "confidence": 0.94,
                    "risk_score": 8.8,
                    "risk_level": "CRITICAL",
                    "evidence": [
                        {
                            "factor": "High Fire Radiative Power",
                            "value": "115.4 MW",
                            "impact": "Indicates intense active thermal combustion",
                            "weight": 0.35,
                        },
                        {
                            "factor": "Vegetation Dryness (NDVI)",
                            "value": "0.15",
                            "impact": "Critically dry fuel bed supporting rapid spread",
                            "weight": 0.25,
                        },
                        {
                            "factor": "SWIR Spectral Anomaly",
                            "value": "3.8",
                            "impact": "Strong active fire spectral signature",
                            "weight": 0.25,
                        },
                    ],
                    "smoke_estimate": {
                        "plume_height_m": 1850.0,
                        "dispersion_direction": 55.0,
                        "pm25_threat_level": "VERY_HIGH",
                        "affected_radius_km": 14.2,
                    },
                    "impact_estimate": {
                        "estimated_burned_ha_24h": 128.5,
                        "containment_difficulty": "EXTREME",
                        "threatened_infrastructure_radius_km": 6.8,
                    },
                }
            ]
        }
    }
