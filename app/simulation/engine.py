import math
from datetime import datetime, timezone
from typing import List
from app.schemas.simulation import SimulationStepData


class SimulationEngine:
    """
    Simulation engine for spatial fire spread calculations.

    NOTE: The old evaluate_simulation_run() method has been DELETED.
    Classification and risk scoring are now handled by the real intelligence
    pipeline (app.intelligence.classifier + app.intelligence.risk).
    This engine only handles geometric spread simulation.
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
        Calculates realistic expansion elliptical coordinates skewed along wind direction.
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
