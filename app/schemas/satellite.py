from datetime import datetime
from pydantic import BaseModel, Field


class SatelliteEvidenceResponse(BaseModel):
    """Detailed satellite evidence for a wildfire target."""
    target_id: str
    satellite: str
    acquisition_time: datetime
    spatial_resolution: str
    swir_anomaly_detected: bool
    swir_band_max_value: float
    smoke_aerosol_index: float
    overlay_geojson_url: str
    preview_thumbnail: str
