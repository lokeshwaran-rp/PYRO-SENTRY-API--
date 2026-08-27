from fastapi import APIRouter, HTTPException, status
from app.schemas.gis import GeoJSONFeatureCollection
from app.services.mock_data import get_gis_feature_collection

router = APIRouter(prefix="/gis", tags=["GIS Layers"])


@router.get("/hotspots", response_model=GeoJSONFeatureCollection, summary="Get Hotspots GeoJSON Layer")
async def get_hotspots_gis():
    """Retrieve GeoJSON FeatureCollection of all active hotspots."""
    data = get_gis_feature_collection("hotspots")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data


@router.get("/targets", response_model=GeoJSONFeatureCollection, summary="Get Targets GeoJSON Layer")
async def get_targets_gis():
    """Retrieve GeoJSON FeatureCollection of identified wildfire target points."""
    data = get_gis_feature_collection("targets")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data


@router.get("/industrial-assets", response_model=GeoJSONFeatureCollection, summary="Get Industrial Assets GeoJSON Layer")
async def get_assets_gis():
    """Retrieve GeoJSON FeatureCollection of industrial infrastructure and critical assets."""
    data = get_gis_feature_collection("industrial-assets")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data


@router.get("/clusters", response_model=GeoJSONFeatureCollection, summary="Get Clusters GeoJSON Layer")
async def get_clusters_gis():
    """Retrieve GeoJSON FeatureCollection of spatial hotspot cluster polygons."""
    data = get_gis_feature_collection("clusters")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data


@router.get("/risk-zones", response_model=GeoJSONFeatureCollection, summary="Get Risk Zones GeoJSON Layer")
async def get_risk_zones_gis():
    """Retrieve GeoJSON FeatureCollection of calculated threat buffer and risk zone polygons."""
    data = get_gis_feature_collection("risk-zones")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data
