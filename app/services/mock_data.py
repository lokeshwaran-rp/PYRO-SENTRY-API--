"""
In-memory mock data store for PYRO-SENTRY REST APIs.
Provides realistic wildfire surveillance data without connecting to a real database.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import copy

# Mock Hotspots
MOCK_HOTSPOTS: List[Dict[str, Any]] = [
    {
        "id": "hs-101",
        "latitude": 34.2439,
        "longitude": -118.1753,
        "frp": 124.5,
        "confidence": 92.0,
        "satellite": "MODIS_Terra",
        "detected_at": "2026-08-26T20:15:00Z",
        "target_id": "tgt-001",
    },
    {
        "id": "hs-102",
        "latitude": 34.2480,
        "longitude": -118.1710,
        "frp": 88.2,
        "confidence": 85.0,
        "satellite": "VIIRS_NOAA20",
        "detected_at": "2026-08-26T20:30:00Z",
        "target_id": "tgt-001",
    },
    {
        "id": "hs-103",
        "latitude": 34.0928,
        "longitude": -117.9250,
        "frp": 45.0,
        "confidence": 78.0,
        "satellite": "VIIRS_SuomiNPP",
        "detected_at": "2026-08-26T21:00:00Z",
        "target_id": "tgt-002",
    },
    {
        "id": "hs-104",
        "latitude": 33.8821,
        "longitude": -117.5810,
        "frp": 210.3,
        "confidence": 98.0,
        "satellite": "GOES-16",
        "detected_at": "2026-08-26T21:10:00Z",
        "target_id": "tgt-003",
    },
]

# Mock Targets and sub-resources
MOCK_TARGETS: Dict[str, Dict[str, Any]] = {
    "tgt-001": {
        "id": "tgt-001",
        "name": "Angeles Canyon Hotspot Complex",
        "status": "ACTIVE",
        "latitude": 34.2459,
        "longitude": -118.1731,
        "estimated_area_ha": 48.6,
        "max_frp": 124.5,
        "confidence_score": 0.94,
        "first_detected": "2026-08-26T18:30:00Z",
        "last_updated": "2026-08-26T21:20:00Z",
        "threat_level": "HIGH",
        "observations": [
            {
                "observation_id": "obs-901",
                "timestamp": "2026-08-26T18:30:00Z",
                "sensor": "VIIRS",
                "frp": 65.4,
                "brightness_temp_k": 342.1,
                "confidence": 88.0,
            },
            {
                "observation_id": "obs-902",
                "timestamp": "2026-08-26T20:30:00Z",
                "sensor": "MODIS",
                "frp": 124.5,
                "brightness_temp_k": 389.4,
                "confidence": 95.0,
            },
        ],
        "history": [
            {
                "event": "TARGET_DETECTED",
                "timestamp": "2026-08-26T18:30:00Z",
                "details": "Initial cluster of 2 thermal detections identified.",
            },
            {
                "event": "THREAT_ESCALATION",
                "timestamp": "2026-08-26T20:00:00Z",
                "details": "FRP increased beyond 100 MW threshold. Threat level set to HIGH.",
            },
        ],
        "classification": {
            "target_id": "tgt-001",
            "primary_class": "WILDFIRE",
            "confidence": 0.93,
            "probabilities": {
                "WILDFIRE": 0.93,
                "PRESCRIBED_BURN": 0.04,
                "INDUSTRIAL_FLARE": 0.02,
                "FALSE_POSITIVE": 0.01,
            },
            "model_version": "v2.4-convnet",
            "evaluated_at": "2026-08-26T20:35:00Z",
        },
        "risk": {
            "target_id": "tgt-001",
            "risk_score": 8.7,
            "risk_category": "CRITICAL",
            "proximity_to_assets_km": 1.2,
            "threatened_assets": ["High Voltage Transmission Line 4A", "Eldorado Ridge Telecom Tower"],
            "wind_speed_kmh": 28.0,
            "wind_direction": "NE",
            "rate_of_spread_m_min": 14.5,
        },
        "evidence": {
            "target_id": "tgt-001",
            "evidence_count": 4,
            "items": [
                {"type": "THERMAL_ANOMALY", "sensor": "VIIRS I-Band", "value": "389.4 K", "weight": 0.4},
                {"type": "SMOKE_PLUME_DETECTED", "sensor": "Sentinel-2", "value": "Visible SWIR plume", "weight": 0.3},
                {"type": "VEGETATION_DRYNESS", "source": "NDVI", "value": "0.18 (Extremely Dry)", "weight": 0.2},
                {"type": "LOW_HUMIDITY", "source": "Weather Station Echo-3", "value": "11% RH", "weight": 0.1},
            ],
        },
        "satellite": {
            "target_id": "tgt-001",
            "satellite": "Sentinel-2B",
            "pass_time": "2026-08-26T19:45:00Z",
            "cloud_cover_pct": 2.1,
            "bands_available": ["B02_BLUE", "B03_GREEN", "B04_RED", "B08_NIR", "B12_SWIR"],
            "image_url": "https://images.pyro-sentry.local/passes/tgt-001-sentinel2-swir.jpg",
            "ground_resolution_m": 10.0,
        },
    },
    "tgt-002": {
        "id": "tgt-002",
        "name": "San Dimas Foothills Hotspot",
        "status": "MONITORING",
        "latitude": 34.0928,
        "longitude": -117.9250,
        "estimated_area_ha": 12.0,
        "max_frp": 45.0,
        "confidence_score": 0.81,
        "first_detected": "2026-08-26T20:00:00Z",
        "last_updated": "2026-08-26T21:00:00Z",
        "threat_level": "MEDIUM",
        "observations": [
            {
                "observation_id": "obs-903",
                "timestamp": "2026-08-26T21:00:00Z",
                "sensor": "VIIRS_SuomiNPP",
                "frp": 45.0,
                "brightness_temp_k": 325.0,
                "confidence": 78.0,
            }
        ],
        "history": [
            {
                "event": "TARGET_DETECTED",
                "timestamp": "2026-08-26T20:00:00Z",
                "details": "Thermal anomaly detected near foothills.",
            }
        ],
        "classification": {
            "target_id": "tgt-002",
            "primary_class": "PRESCRIBED_BURN",
            "confidence": 0.65,
            "probabilities": {
                "WILDFIRE": 0.25,
                "PRESCRIBED_BURN": 0.65,
                "INDUSTRIAL_FLARE": 0.05,
                "FALSE_POSITIVE": 0.05,
            },
            "model_version": "v2.4-convnet",
            "evaluated_at": "2026-08-26T20:10:00Z",
        },
        "risk": {
            "target_id": "tgt-002",
            "risk_score": 4.2,
            "risk_category": "MODERATE",
            "proximity_to_assets_km": 5.4,
            "threatened_assets": ["Residential Perimeter Zone B"],
            "wind_speed_kmh": 12.0,
            "wind_direction": "SW",
            "rate_of_spread_m_min": 4.1,
        },
        "evidence": {
            "target_id": "tgt-002",
            "evidence_count": 2,
            "items": [
                {"type": "THERMAL_ANOMALY", "sensor": "VIIRS", "value": "325 K", "weight": 0.6},
                {"type": "PERMIT_MATCH", "source": "Forestry DB", "value": "Agricultural clearance permit", "weight": 0.4},
            ],
        },
        "satellite": {
            "target_id": "tgt-002",
            "satellite": "Landsat-9",
            "pass_time": "2026-08-26T20:15:00Z",
            "cloud_cover_pct": 5.0,
            "bands_available": ["B4_RED", "B5_NIR", "B7_SWIR2"],
            "image_url": "https://images.pyro-sentry.local/passes/tgt-002-landsat9.jpg",
            "ground_resolution_m": 30.0,
        },
    },
}

# Mock Threats (Stateful in-memory collection)
MOCK_THREATS: List[Dict[str, Any]] = [
    {
        "id": "threat-501",
        "target_id": "tgt-001",
        "title": "Threat to Transmission Corridor 4A",
        "severity": "CRITICAL",
        "status": "OPEN",
        "risk_score": 8.7,
        "impact_zone": "Angeles National Forest - North Corridor",
        "reported_at": "2026-08-26T20:05:00Z",
        "acknowledged_at": None,
        "acknowledged_by": None,
        "resolved_at": None,
        "notes": "Fire spreading northeast towards power infrastructure.",
    },
    {
        "id": "threat-502",
        "target_id": "tgt-002",
        "title": "Smoke Inversion in San Dimas Valley",
        "severity": "MEDIUM",
        "status": "ACKNOWLEDGED",
        "risk_score": 4.2,
        "impact_zone": "San Dimas Foothills",
        "reported_at": "2026-08-26T20:20:00Z",
        "acknowledged_at": "2026-08-26T20:45:00Z",
        "acknowledged_by": "Operator_08",
        "resolved_at": None,
        "notes": "Local fire dispatch notified.",
    },
]

# Mock Industrial Assets
MOCK_INDUSTRIAL_ASSETS: List[Dict[str, Any]] = [
    {
        "id": "asset-01",
        "name": "Transmission Line 4A Pylon 12",
        "type": "POWER_GRID",
        "latitude": 34.2510,
        "longitude": -118.1620,
        "criticality": "HIGH",
    },
    {
        "id": "asset-02",
        "name": "Eldorado Ridge Telecom Tower",
        "type": "COMMUNICATIONS",
        "latitude": 34.2600,
        "longitude": -118.1700,
        "criticality": "CRITICAL",
    },
    {
        "id": "asset-03",
        "name": "Mountain Water Pumping Station #3",
        "type": "WATER_UTILITY",
        "latitude": 34.2380,
        "longitude": -118.1850,
        "criticality": "MEDIUM",
    },
]

# Mock Analytics Datasets
MOCK_ANALYTICS_SUMMARY: Dict[str, Any] = {
    "active_targets_count": 2,
    "total_hotspots_detected_24h": 4,
    "critical_threats_count": 1,
    "total_estimated_burned_ha": 60.6,
    "average_confidence_pct": 88.5,
    "highest_frp_mw": 124.5,
    "last_updated": "2026-08-26T21:30:00Z",
}

MOCK_FRP_TRENDS: List[Dict[str, Any]] = [
    {"timestamp": "2026-08-26T16:00:00Z", "total_frp_mw": 15.2, "hotspots_count": 1},
    {"timestamp": "2026-08-26T17:00:00Z", "total_frp_mw": 28.6, "hotspots_count": 2},
    {"timestamp": "2026-08-26T18:00:00Z", "total_frp_mw": 65.4, "hotspots_count": 2},
    {"timestamp": "2026-08-26T19:00:00Z", "total_frp_mw": 89.0, "hotspots_count": 3},
    {"timestamp": "2026-08-26T20:00:00Z", "total_frp_mw": 182.7, "hotspots_count": 4},
    {"timestamp": "2026-08-26T21:00:00Z", "total_frp_mw": 212.7, "hotspots_count": 4},
]

MOCK_CLASSIFICATION_DISTRIBUTION: Dict[str, int] = {
    "WILDFIRE": 18,
    "PRESCRIBED_BURN": 4,
    "INDUSTRIAL_FLARE": 2,
    "FALSE_POSITIVE": 1,
}

MOCK_HOURLY_ACTIVITY: List[Dict[str, Any]] = [
    {"hour_utc": f"{h:02d}:00", "detections": count}
    for h, count in enumerate([0, 0, 1, 0, 0, 0, 2, 5, 8, 12, 18, 25, 30, 28, 22, 19, 14, 10, 6, 4, 3, 2, 1, 0])
]

# Mock Satellite Evidence
MOCK_SATELLITE_EVIDENCE: Dict[str, Dict[str, Any]] = {
    "tgt-001": {
        "target_id": "tgt-001",
        "satellite": "Sentinel-2B / MSI",
        "acquisition_time": "2026-08-26T19:45:00Z",
        "spatial_resolution": "10m",
        "swir_anomaly_detected": True,
        "swir_band_max_value": 4.12,
        "smoke_aerosol_index": 3.8,
        "overlay_geojson_url": "https://api.pyro-sentry.local/overlays/tgt-001.geojson",
        "preview_thumbnail": "https://api.pyro-sentry.local/thumbs/tgt-001.jpg",
    },
    "tgt-002": {
        "target_id": "tgt-002",
        "satellite": "Landsat-9 / OLI-2",
        "acquisition_time": "2026-08-26T20:15:00Z",
        "spatial_resolution": "30m",
        "swir_anomaly_detected": True,
        "swir_band_max_value": 1.95,
        "smoke_aerosol_index": 1.2,
        "overlay_geojson_url": "https://api.pyro-sentry.local/overlays/tgt-002.geojson",
        "preview_thumbnail": "https://api.pyro-sentry.local/thumbs/tgt-002.jpg",
    },
}

# Mock Data Sources
MOCK_DATA_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "NASA FIRMS (MODIS/VIIRS)",
        "type": "THERMAL_HOTSPOT_FEED",
        "status": "ONLINE",
        "last_sync": "2026-08-26T21:28:00Z",
        "ping_ms": 142,
        "items_ingested_last_hour": 14,
    },
    {
        "name": "NOAA GOES-East / GOES-West",
        "type": "GEOSTATIONARY_FIRE_FEED",
        "status": "ONLINE",
        "last_sync": "2026-08-26T21:29:30Z",
        "ping_ms": 89,
        "items_ingested_last_hour": 52,
    },
    {
        "name": "Copernicus Sentinel-2 Hub",
        "type": "HIGH_RES_OPTICAL_FEED",
        "status": "ONLINE",
        "last_sync": "2026-08-26T21:15:00Z",
        "ping_ms": 310,
        "items_ingested_last_hour": 2,
    },
    {
        "name": "National Weather Service (NOAA NWS)",
        "type": "METEOROLOGY_FEED",
        "status": "ONLINE",
        "last_sync": "2026-08-26T21:25:00Z",
        "ping_ms": 65,
        "items_ingested_last_hour": 120,
    },
]

# Mock System Status
MOCK_SYSTEM_STATUS: Dict[str, Any] = {
    "system_name": "PYRO-SENTRY Wildfire Intelligence Platform",
    "version": "1.0.0",
    "status": "OPERATIONAL",
    "uptime_seconds": 128450,
    "pipeline_latency_ms": 320,
    "active_modules": [
        "REST_API_GATEWAY",
        "WEBSOCKET_BROADCASTER",
        "SIMULATION_ORCHESTRATOR",
        "MOCK_FEED_INGESTION",
    ],
    "memory_usage_mb": 145.2,
    "cpu_load_pct": 3.8,
}


# --- Accessor & Mutation Helpers ---

def get_hotspots(min_frp: Optional[float] = None, min_confidence: Optional[float] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve hotspots with optional filtering."""
    results = MOCK_HOTSPOTS
    if min_frp is not None:
        results = [h for h in results if h["frp"] >= min_frp]
    if min_confidence is not None:
        results = [h for h in results if h["confidence"] >= min_confidence]
    return results[:limit]


def get_targets(status: Optional[str] = None, threat_level: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve list of targets."""
    results = list(MOCK_TARGETS.values())
    if status is not None:
        results = [t for t in results if t["status"].upper() == status.upper()]
    if threat_level is not None:
        results = [t for t in results if t["threat_level"].upper() == threat_level.upper()]
    return results[:limit]


def get_target_by_id(target_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a target by its ID."""
    return MOCK_TARGETS.get(target_id)


def get_target_subresource(target_id: str, subresource: str) -> Optional[Any]:
    """Retrieve a subresource (observations, history, classification, risk, evidence, satellite) for target."""
    target = get_target_by_id(target_id)
    if not target:
        return None
    return target.get(subresource)


def get_threats(status: Optional[str] = None, severity: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve threats."""
    results = MOCK_THREATS
    if status is not None:
        results = [t for t in results if t["status"].upper() == status.upper()]
    if severity is not None:
        results = [t for t in results if t["severity"].upper() == severity.upper()]
    return results[:limit]


def get_threat_by_id(threat_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single threat by ID."""
    for threat in MOCK_THREATS:
        if threat["id"] == threat_id:
            return threat
    return None


def patch_threat(threat_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Apply partial update to a threat."""
    threat = get_threat_by_id(threat_id)
    if not threat:
        return None
    for key, val in updates.items():
        if val is not None:
            threat[key] = val
    return threat


def acknowledge_threat(threat_id: str, operator_name: str = "Default_Operator") -> Optional[Dict[str, Any]]:
    """Mark a threat as acknowledged."""
    threat = get_threat_by_id(threat_id)
    if not threat:
        return None
    threat["status"] = "ACKNOWLEDGED"
    threat["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
    threat["acknowledged_by"] = operator_name
    return threat


def resolve_threat(threat_id: str, resolution_notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Mark a threat as resolved."""
    threat = get_threat_by_id(threat_id)
    if not threat:
        return None
    threat["status"] = "RESOLVED"
    threat["resolved_at"] = datetime.now(timezone.utc).isoformat()
    if resolution_notes:
        threat["notes"] = f"{threat.get('notes', '')} | Resolution: {resolution_notes}"
    return threat


def get_satellite_evidence(target_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve satellite evidence for a target."""
    return MOCK_SATELLITE_EVIDENCE.get(target_id)


def search_all(query: str) -> Dict[str, Any]:
    """Perform keyword search across targets, threats, and assets."""
    q = query.lower()
    matched_targets = [
        {"id": t["id"], "type": "TARGET", "title": t["name"], "details": f"Status: {t['status']}, Area: {t['estimated_area_ha']} ha"}
        for t in MOCK_TARGETS.values()
        if q in t["name"].lower() or q in t["id"].lower() or q in t["threat_level"].lower()
    ]
    matched_threats = [
        {"id": t["id"], "type": "THREAT", "title": t["title"], "details": f"Severity: {t['severity']}, Status: {t['status']}"}
        for t in MOCK_THREATS
        if q in t["title"].lower() or q in t["id"].lower() or q in t["severity"].lower() or q in t["impact_zone"].lower()
    ]
    matched_assets = [
        {"id": a["id"], "type": "ASSET", "title": a["name"], "details": f"Type: {a['type']}, Criticality: {a['criticality']}"}
        for a in MOCK_INDUSTRIAL_ASSETS
        if q in a["name"].lower() or q in a["id"].lower() or q in a["type"].lower()
    ]

    return {
        "query": query,
        "total_results": len(matched_targets) + len(matched_threats) + len(matched_assets),
        "results": {
            "targets": matched_targets,
            "threats": matched_threats,
            "assets": matched_assets,
        },
    }


def get_gis_feature_collection(layer_name: str) -> Optional[Dict[str, Any]]:
    """Generate GeoJSON FeatureCollection for requested GIS layer."""
    if layer_name == "hotspots":
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [h["longitude"], h["latitude"]],
                },
                "properties": {
                    "id": h["id"],
                    "frp": h["frp"],
                    "confidence": h["confidence"],
                    "satellite": h["satellite"],
                    "detected_at": h["detected_at"],
                },
            }
            for h in MOCK_HOTSPOTS
        ]
    elif layer_name == "targets":
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [t["longitude"], t["latitude"]],
                },
                "properties": {
                    "id": t["id"],
                    "name": t["name"],
                    "status": t["status"],
                    "threat_level": t["threat_level"],
                    "max_frp": t["max_frp"],
                    "estimated_area_ha": t["estimated_area_ha"],
                },
            }
            for t in MOCK_TARGETS.values()
        ]
    elif layer_name == "industrial-assets":
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [a["longitude"], a["latitude"]],
                },
                "properties": {
                    "id": a["id"],
                    "name": a["name"],
                    "type": a["type"],
                    "criticality": a["criticality"],
                },
            }
            for a in MOCK_INDUSTRIAL_ASSETS
        ]
    elif layer_name == "clusters":
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-118.180, 34.240],
                            [-118.170, 34.240],
                            [-118.170, 34.250],
                            [-118.180, 34.250],
                            [-118.180, 34.240],
                        ]
                    ],
                },
                "properties": {
                    "cluster_id": "cluster-canyon-01",
                    "hotspot_count": 2,
                    "avg_frp": 106.35,
                    "target_id": "tgt-001",
                },
            }
        ]
    elif layer_name == "risk-zones":
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-118.190, 34.230],
                            [-118.160, 34.230],
                            [-118.160, 34.260],
                            [-118.190, 34.260],
                            [-118.190, 34.230],
                        ]
                    ],
                },
                "properties": {
                    "zone_id": "risk-zone-red-01",
                    "risk_level": "EXTREME",
                    "buffer_radius_km": 2.5,
                    "evacuation_warning": True,
                },
            }
        ]
    else:
        return None

    return {
        "type": "FeatureCollection",
        "layer_name": layer_name,
        "features": features,
    }
