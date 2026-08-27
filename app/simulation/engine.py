import math
from datetime import datetime, timezone
from typing import List
from app.schemas.simulation import (
    SimulationStepData,
    SimulationRunRequest,
    SimulationRunResponse,
    SimulationEvidenceItem,
    SimulationSmokeEstimate,
    SimulationImpactEstimate,
)


class SimulationEngine:
    """
    Lightweight simulation engine that computes:
    1. Spatial spreading perimeters for active time-series simulations.
    2. Stateless mock classification and risk evaluation for POST /api/v1/simulation/run.
    """

    @staticmethod
    def generate_step(
        simulation_id: str,
        step_number: int,
        origin_lat: float,
        origin_lon: float,
        wind_speed_kmh: float,
        wind_direction_deg: float,
    ) -> SimulationStepData:
        """
        Generate a single simulation step with spreading perimeter points.
        Calculates realistic mock expansion elliptical coordinates skewed along wind direction.
        """
        rad = math.radians(wind_direction_deg)
        growth_factor = step_number * 0.002
        wind_bias = (wind_speed_kmh / 50.0) * growth_factor

        perimeter_points: List[List[float]] = []
        num_vertices = 8
        for i in range(num_vertices):
            angle = 2 * math.pi * (i / num_vertices)
            r_lat = growth_factor * (1.0 + 0.5 * math.cos(angle - rad))
            r_lon = growth_factor * (1.0 + 0.5 * math.sin(angle - rad))
            lat_offset = math.cos(angle) * r_lat + (wind_bias * math.cos(rad))
            lon_offset = math.sin(angle) * r_lon + (wind_bias * math.sin(rad))

            point_lat = round(origin_lat + lat_offset, 6)
            point_lon = round(origin_lon + lon_offset, 6)
            perimeter_points.append([point_lat, point_lon])

        perimeter_points.append(perimeter_points[0])
        burned_area = round(step_number * (12.5 + (wind_speed_kmh * 0.8)), 2)
        containment = min(100.0, max(5.0, round(10.0 + (step_number * 3.5), 1)))

        return SimulationStepData(
            simulation_id=simulation_id,
            step_number=step_number,
            timestamp=datetime.now(timezone.utc),
            burned_area_hectares=burned_area,
            front_coordinates=perimeter_points,
            containment_pct=containment,
        )

    @staticmethod
    def evaluate_simulation_run(req: SimulationRunRequest) -> SimulationRunResponse:
        """
        Stateless mock evaluation logic for a single feature vector input.
        Does NOT modify any external state, targets, or threats.
        """
        evidence_items: List[SimulationEvidenceItem] = []

        # 1. Mock Classification Rule Evaluator
        if req.industrial_proximity <= 0.8 and req.frp < 80.0:
            classification = "INDUSTRIAL_FLARE"
            confidence = round(min(0.98, 0.75 + (0.8 - req.industrial_proximity) * 0.25), 2)
            base_risk = 2.5
            evidence_items.append(SimulationEvidenceItem(
                factor="Industrial Proximity",
                value=f"{req.industrial_proximity} km",
                impact="High spatial alignment with industrial facility / flare stack",
                weight=0.45,
            ))
        elif req.ndvi > 0.65 and req.brightness < 315.0 and req.frp < 30.0:
            classification = "FALSE_POSITIVE"
            confidence = 0.85
            base_risk = 1.0
            evidence_items.append(SimulationEvidenceItem(
                factor="High Vegetation Moisture & Low Temp",
                value=f"NDVI={req.ndvi}, Temp={req.brightness}K",
                impact="Thermal signal likely caused by solar reflectance or sensor artifact",
                weight=0.50,
            ))
        elif req.frp < 40.0 and req.persistence <= 2 and req.wind_speed < 15.0 and req.nbr > 0.1:
            classification = "PRESCRIBED_BURN"
            confidence = 0.78
            base_risk = 3.8
            evidence_items.append(SimulationEvidenceItem(
                factor="Controlled Thermal Signature",
                value=f"FRP={req.frp} MW, NBR={req.nbr}",
                impact="Low rate of spread with moderate localized heat signature",
                weight=0.35,
            ))
        else:
            classification = "WILDFIRE"
            # High confidence if high FRP, low NDVI, high SWIR
            conf_score = 0.70 + (min(150.0, req.frp) / 500.0) + (req.swir_anomaly * 0.04)
            confidence = round(min(0.99, conf_score), 2)
            base_risk = 6.0
            evidence_items.append(SimulationEvidenceItem(
                factor="High Thermal Intensity (FRP)",
                value=f"{req.frp} MW",
                impact="Substantial convective energy detected",
                weight=0.35,
            ))

        # Add common supporting evidence
        if req.ndvi < 0.25:
            evidence_items.append(SimulationEvidenceItem(
                factor="Dry Vegetation Fuel (NDVI)",
                value=f"{req.ndvi}",
                impact="Low moisture fuel bed increases ignition and spread potential",
                weight=0.25,
            ))
        if req.swir_anomaly > 2.0:
            evidence_items.append(SimulationEvidenceItem(
                factor="SWIR Infrared Anomaly",
                value=f"{req.swir_anomaly}",
                impact="Strong shortwave infrared reflection confirms active combustion",
                weight=0.20,
            ))
        if req.wind_speed > 20.0:
            evidence_items.append(SimulationEvidenceItem(
                factor="Elevated Wind Velocity",
                value=f"{req.wind_speed} km/h",
                impact="High wind accelerates forward fire line advancement",
                weight=0.20,
            ))

        # 2. Compute Composite Risk Score (0.0 - 10.0)
        risk_adjustment = (req.wind_speed * 0.05) + (req.frp * 0.015) + (req.persistence * 0.3)
        if req.industrial_proximity < 2.0:
            risk_adjustment += (2.0 - req.industrial_proximity) * 0.8

        calculated_risk = round(min(10.0, max(0.5, base_risk + risk_adjustment)), 1)

        # Determine Risk Level
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

        # 3. Compute Smoke Estimate
        smoke_est = SimulationSmokeEstimate(
            plume_height_m=round(500.0 + (req.frp * 12.0), 1),
            dispersion_direction=req.wind_direction,
            pm25_threat_level=pm25_level,
            affected_radius_km=round(2.0 + (req.wind_speed * 0.45) + (req.frp * 0.04), 1),
        )

        # 4. Compute Impact Estimate
        impact_est = SimulationImpactEstimate(
            estimated_burned_ha_24h=round(10.0 + (req.frp * 0.9) + (req.wind_speed * 1.5), 1),
            containment_difficulty=difficulty,
            threatened_infrastructure_radius_km=round(1.0 + (req.wind_speed * 0.15) + (calculated_risk * 0.4), 1),
        )

        return SimulationRunResponse(
            is_simulated=True,
            simulation_mode="SIMULATED",
            simulation_timestamp=datetime.now(timezone.utc),
            status="COMPLETED",
            classification=classification,
            confidence=confidence,
            risk_score=calculated_risk,
            risk_level=risk_level,
            evidence=evidence_items,
            smoke_estimate=smoke_est,
            impact_estimate=impact_est,
        )
