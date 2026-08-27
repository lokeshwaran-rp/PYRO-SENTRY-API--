from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GeoJSONGeometry(BaseModel):
    """Geometry object for GeoJSON."""
    type: str
    coordinates: Any


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature representation."""
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection container."""
    type: str = "FeatureCollection"
    layer_name: Optional[str] = None
    features: List[GeoJSONFeature]
