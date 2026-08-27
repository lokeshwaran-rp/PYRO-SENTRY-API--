from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.gis import GeoJSONFeatureCollection
from app.db.session import get_db
from app.services.db_service import get_gis_feature_collection
from app.auth.security import get_current_user

router = APIRouter(prefix="/gis", tags=["GIS Layers"])


@router.get("/hotspots", response_model=GeoJSONFeatureCollection, summary="Get Hotspots GeoJSON Layer")
async def get_hotspots_gis(db: AsyncSession = Depends(get_db), _current_user=Depends(get_current_user)):
    """Retrieve GeoJSON FeatureCollection of all active hotspots."""
    data = await get_gis_feature_collection(db, "hotspots")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data


@router.get("/targets", response_model=GeoJSONFeatureCollection, summary="Get Targets GeoJSON Layer")
async def get_targets_gis(db: AsyncSession = Depends(get_db), _current_user=Depends(get_current_user)):
    """Retrieve GeoJSON FeatureCollection of identified target points."""
    data = await get_gis_feature_collection(db, "targets")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data


@router.get("/industrial-assets", response_model=GeoJSONFeatureCollection, summary="Get Industrial Assets GeoJSON Layer")
async def get_assets_gis(db: AsyncSession = Depends(get_db), _current_user=Depends(get_current_user)):
    """Retrieve GeoJSON FeatureCollection of industrial infrastructure and critical assets."""
    data = await get_gis_feature_collection(db, "industrial-assets")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data


@router.get("/clusters", response_model=GeoJSONFeatureCollection, summary="Get Clusters GeoJSON Layer")
async def get_clusters_gis(db: AsyncSession = Depends(get_db), _current_user=Depends(get_current_user)):
    """Retrieve GeoJSON FeatureCollection of spatial hotspot cluster polygons."""
    data = await get_gis_feature_collection(db, "clusters")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data


@router.get("/risk-zones", response_model=GeoJSONFeatureCollection, summary="Get Risk Zones GeoJSON Layer")
async def get_risk_zones_gis(db: AsyncSession = Depends(get_db), _current_user=Depends(get_current_user)):
    """Retrieve GeoJSON FeatureCollection of calculated threat buffer and risk zone polygons."""
    data = await get_gis_feature_collection(db, "risk-zones")
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")
    return data
