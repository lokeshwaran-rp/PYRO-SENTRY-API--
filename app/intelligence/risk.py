"""
PYRO-SENTRY Real Risk Scorer.

Single source of truth for composite risk scoring.
Both the live pipeline and /simulation/run call this — no divergence possible.
"""

from dataclasses import dataclass
from .classifier import ClassificationResult


@dataclass
class SmokeEstimate:
    """Smoke dispersion and plume metrics."""
    plume_height_m: float
    dispersion_direction: float
    pm25_threat_level: str
    affected_radius_km: float


@dataclass
class ImpactEstimate:
    """Impact assessment metrics."""
    estimated_burned_ha_24h: float
    containment_difficulty: str
    threatened_infrastructure_radius_km: float


@dataclass
class RiskResult:
    """Output of the risk scorer."""
    risk_score: float
    risk_level: str
    smoke_estimate: SmokeEstimate
    impact_estimate: ImpactEstimate


def compute_risk(
    frp: float,
    brightness: float,
    persistence: int,
    industrial_proximity: float,
    wind_speed: float,
    wind_direction: float,
    ndvi: float,
    nbr: float,
    swir_anomaly: float,
    classification: ClassificationResult,
) -> RiskResult:
    """
    Compute composite risk score and related estimates.

    This function is the SINGLE SOURCE OF TRUTH for risk scoring.
    Both live pipeline processing and simulation/run call this function.

    Args:
        frp: Fire Radiative Power in MW
        brightness: Brightness temperature in Kelvin
        persistence: Consecutive detection count
        industrial_proximity: Distance in km to nearest facility
        wind_speed: Wind speed in km/h
        wind_direction: Wind azimuth (0-360)
        ndvi: Normalized Difference Vegetation Index
        nbr: Normalized Burn Ratio
        swir_anomaly: SWIR anomaly index
        classification: ClassificationResult from classifier

    Returns:
        RiskResult with risk_score, risk_level, smoke_estimate, and impact_estimate.
    """
    # ─── Base risk by classification ─────────────────────────────────────
    base_risk_map = {
        "WILDFIRE": 6.0,
        "PRESCRIBED_BURN": 3.8,
        "INDUSTRIAL_FLARE": 2.5,
        "FALSE_POSITIVE": 1.0,
    }
    base_risk = base_risk_map.get(classification.primary_class, 5.0)

    # ─── Risk adjustment factors ─────────────────────────────────────────
    risk_adjustment = (wind_speed * 0.05) + (frp * 0.015) + (persistence * 0.3)
    if industrial_proximity < 2.0:
        risk_adjustment += (2.0 - industrial_proximity) * 0.8

    calculated_risk = round(min(10.0, max(0.5, base_risk + risk_adjustment)), 1)

    # ─── Risk level determination ────────────────────────────────────────
    if calculated_risk >= 8.0:
        risk_level = "CRITICAL"
        difficulty = "EXTREME"
        pm25_level = "VERY_HIGH"
    elif calculated_risk >= 6.0:
        risk_level = "HIGH"
        difficulty = "HIGH"
        pm25_level = "HIGH"
    elif calculated_risk >= 3.5:
        risk_level = "MODERATE"
        difficulty = "MODERATE"
        pm25_level = "MODERATE"
    else:
        risk_level = "LOW"
        difficulty = "LOW"
        pm25_level = "LOW"

    # ─── Smoke estimate ──────────────────────────────────────────────────
    smoke_estimate = SmokeEstimate(
        plume_height_m=round(500.0 + (frp * 12.0), 1),
        dispersion_direction=wind_direction,
        pm25_threat_level=pm25_level,
        affected_radius_km=round(2.0 + (wind_speed * 0.45) + (frp * 0.04), 1),
    )

    # ─── Impact estimate ─────────────────────────────────────────────────
    impact_estimate = ImpactEstimate(
        estimated_burned_ha_24h=round(10.0 + (frp * 0.9) + (wind_speed * 1.5), 1),
        containment_difficulty=difficulty,
        threatened_infrastructure_radius_km=round(
            1.0 + (wind_speed * 0.15) + (calculated_risk * 0.4), 1
        ),
    )

    return RiskResult(
        risk_score=calculated_risk,
        risk_level=risk_level,
        smoke_estimate=smoke_estimate,
        impact_estimate=impact_estimate,
    )
