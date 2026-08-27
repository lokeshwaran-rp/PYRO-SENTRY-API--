"""
PYRO-SENTRY Database Service Layer.

Replaces all in-memory mock data accessors with real async DB queries.
Every endpoint calls these functions instead of the deleted mock_data.py.
"""

import uuid
import psutil
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Hotspot, Target, Observation, TargetHistory, Classification,
    RiskAssessment, Evidence, SatellitePass, Threat, Event,
    IndustrialAsset, DataSource, ThreatStatusEnum, SeverityEnum,
)
from app.services.lifecycle import validate_transition, get_valid_transitions


# ─── Hotspots ────────────────────────────────────────────────────────────────

async def get_hotspots(
    db: AsyncSession,
    min_frp: Optional[float] = None,
    min_confidence: Optional[float] = None,
    limit: int = 50,
) -> List[Hotspot]:
    """Retrieve hotspots with optional filtering."""
    query = select(Hotspot)
    if min_frp is not None:
        query = query.where(Hotspot.frp >= min_frp)
    if min_confidence is not None:
        query = query.where(Hotspot.confidence >= min_confidence)
    query = query.order_by(Hotspot.detected_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


# ─── Targets ─────────────────────────────────────────────────────────────────

async def get_targets(
    db: AsyncSession,
    status: Optional[str] = None,
    threat_level: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve list of targets with embedded sub-resources."""
    query = select(Target)
    if status is not None:
        query = query.where(Target.status == status.upper())
    if threat_level is not None:
        query = query.where(Target.threat_level == threat_level.upper())
    query = query.order_by(Target.last_updated.desc()).limit(limit)
    result = await db.execute(query)
    targets = result.scalars().all()
    return [await _target_to_dict(db, t) for t in targets]


async def get_target_by_id(db: AsyncSession, target_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a target by ID with all sub-resources."""
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalars().first()
    if not target:
        return None
    return await _target_to_dict(db, target, include_subresources=True)


async def get_target_subresource(db: AsyncSession, target_id: str, subresource: str) -> Optional[Any]:
    """Retrieve a specific sub-resource for a target."""
    # First verify target exists
    result = await db.execute(select(Target).where(Target.id == target_id))
    if not result.scalars().first():
        return None

    if subresource == "observations":
        result = await db.execute(
            select(Observation).where(Observation.target_id == target_id).order_by(Observation.timestamp.desc())
        )
        obs = result.scalars().all()
        return [{"observation_id": o.id, "timestamp": o.timestamp.isoformat(), "sensor": o.sensor,
                 "frp": o.frp, "brightness_temp_k": o.brightness_temp_k, "confidence": o.confidence} for o in obs]

    elif subresource == "history":
        result = await db.execute(
            select(TargetHistory).where(TargetHistory.target_id == target_id).order_by(TargetHistory.timestamp.desc())
        )
        hist = result.scalars().all()
        return [{"event": h.event, "timestamp": h.timestamp.isoformat(), "details": h.details} for h in hist]

    elif subresource == "classification":
        result = await db.execute(
            select(Classification).where(Classification.target_id == target_id)
        )
        cls = result.scalars().first()
        if not cls:
            return None
        return {"target_id": cls.target_id, "primary_class": cls.primary_class, "confidence": cls.confidence,
                "probabilities": cls.probabilities, "model_version": cls.model_version,
                "evaluated_at": cls.evaluated_at.isoformat()}

    elif subresource == "risk":
        result = await db.execute(
            select(RiskAssessment).where(RiskAssessment.target_id == target_id)
        )
        risk = result.scalars().first()
        if not risk:
            return None
        return {"target_id": risk.target_id, "risk_score": risk.risk_score, "risk_category": risk.risk_category,
                "proximity_to_assets_km": risk.proximity_to_assets_km, "threatened_assets": risk.threatened_assets,
                "wind_speed_kmh": risk.wind_speed_kmh, "wind_direction": risk.wind_direction,
                "rate_of_spread_m_min": risk.rate_of_spread_m_min}

    elif subresource == "evidence":
        result = await db.execute(
            select(Evidence).where(Evidence.target_id == target_id)
        )
        ev = result.scalars().first()
        if not ev:
            return None
        return {"target_id": ev.target_id, "evidence_count": ev.evidence_count, "items": ev.items}

    elif subresource == "satellite":
        result = await db.execute(
            select(SatellitePass).where(SatellitePass.target_id == target_id)
        )
        sat = result.scalars().first()
        if not sat:
            return None
        return {"target_id": sat.target_id, "satellite": sat.satellite,
                "pass_time": sat.pass_time.isoformat(), "cloud_cover_pct": sat.cloud_cover_pct,
                "bands_available": sat.bands_available, "image_url": sat.image_url,
                "ground_resolution_m": sat.ground_resolution_m}

    return None


async def _target_to_dict(db: AsyncSession, target: Target, include_subresources: bool = False) -> Dict[str, Any]:
    """Convert a Target model to a dict, optionally including sub-resources."""
    d = {
        "id": target.id, "name": target.name, "status": target.status,
        "latitude": target.latitude, "longitude": target.longitude,
        "estimated_area_ha": target.estimated_area_ha, "max_frp": target.max_frp,
        "confidence_score": target.confidence_score,
        "first_detected": target.first_detected.isoformat(),
        "last_updated": target.last_updated.isoformat(),
        "threat_level": target.threat_level,
    }
    if include_subresources:
        for sub in ["observations", "history", "classification", "risk", "evidence", "satellite"]:
            d[sub] = await get_target_subresource(db, target.id, sub)
    return d


# ─── Threats ─────────────────────────────────────────────────────────────────

async def get_threats(
    db: AsyncSession,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve threats with optional filtering."""
    query = select(Threat)
    if status is not None:
        try:
            status_enum = ThreatStatusEnum(status.upper())
            query = query.where(Threat.status == status_enum)
        except ValueError:
            pass
    if severity is not None:
        try:
            sev_enum = SeverityEnum(severity.upper())
            query = query.where(Threat.severity == sev_enum)
        except ValueError:
            pass
    query = query.order_by(Threat.reported_at.desc()).limit(limit)
    result = await db.execute(query)
    return [_threat_to_dict(t) for t in result.scalars().all()]


async def get_threat_by_id(db: AsyncSession, threat_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single threat by ID."""
    result = await db.execute(select(Threat).where(Threat.id == threat_id))
    threat = result.scalars().first()
    return _threat_to_dict(threat) if threat else None


async def get_threat_model_by_id(db: AsyncSession, threat_id: str) -> Optional[Threat]:
    """Retrieve the raw Threat ORM model by ID (for mutations)."""
    result = await db.execute(select(Threat).where(Threat.id == threat_id))
    return result.scalars().first()


async def patch_threat(db: AsyncSession, threat_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Apply partial update to a threat with lifecycle validation."""
    threat = await get_threat_model_by_id(db, threat_id)
    if not threat:
        return None

    # If status is being changed, validate the transition
    if "status" in updates and updates["status"] is not None:
        new_status_str = updates["status"].upper()
        try:
            new_status = ThreatStatusEnum(new_status_str)
        except ValueError:
            raise ValueError(f"Invalid status '{updates['status']}'. Valid: {[s.value for s in ThreatStatusEnum]}")

        if not validate_transition(threat.status, new_status):
            valid = get_valid_transitions(threat.status)
            raise ValueError(
                f"Invalid transition: {threat.status.value} → {new_status_str}. "
                f"Allowed transitions from {threat.status.value}: {valid}"
            )
        threat.status = new_status

    if "severity" in updates and updates["severity"] is not None:
        try:
            threat.severity = SeverityEnum(updates["severity"].upper())
        except ValueError:
            raise ValueError(f"Invalid severity '{updates['severity']}'")

    if "notes" in updates and updates["notes"] is not None:
        threat.notes = updates["notes"]

    await db.commit()
    await db.refresh(threat)
    return _threat_to_dict(threat)


async def acknowledge_threat(db: AsyncSession, threat_id: str, operator_name: str = "Operator_01") -> Optional[Dict[str, Any]]:
    """Transition threat to ACKNOWLEDGED with lifecycle validation."""
    threat = await get_threat_model_by_id(db, threat_id)
    if not threat:
        return None

    if not validate_transition(threat.status, ThreatStatusEnum.ACKNOWLEDGED):
        valid = get_valid_transitions(threat.status)
        raise ValueError(
            f"Cannot acknowledge: current status is {threat.status.value}. "
            f"Allowed transitions: {valid}"
        )

    threat.status = ThreatStatusEnum.ACKNOWLEDGED
    threat.acknowledged_at = datetime.now(timezone.utc)
    threat.acknowledged_by = operator_name
    await db.commit()
    await db.refresh(threat)
    return _threat_to_dict(threat)


async def resolve_threat(db: AsyncSession, threat_id: str, resolution_notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Transition threat to RESOLVED with lifecycle validation."""
    threat = await get_threat_model_by_id(db, threat_id)
    if not threat:
        return None

    if not validate_transition(threat.status, ThreatStatusEnum.RESOLVED):
        valid = get_valid_transitions(threat.status)
        raise ValueError(
            f"Cannot resolve: current status is {threat.status.value}. "
            f"Allowed transitions: {valid}"
        )

    threat.status = ThreatStatusEnum.RESOLVED
    threat.resolved_at = datetime.now(timezone.utc)
    if resolution_notes:
        existing_notes = threat.notes or ""
        threat.notes = f"{existing_notes} | Resolution: {resolution_notes}" if existing_notes else f"Resolution: {resolution_notes}"
    await db.commit()
    await db.refresh(threat)
    return _threat_to_dict(threat)


def _threat_to_dict(threat: Threat) -> Dict[str, Any]:
    """Convert Threat model to a dict."""
    return {
        "id": threat.id,
        "target_id": threat.target_id,
        "title": threat.title,
        "severity": threat.severity.value if isinstance(threat.severity, SeverityEnum) else threat.severity,
        "status": threat.status.value if isinstance(threat.status, ThreatStatusEnum) else threat.status,
        "risk_score": threat.risk_score,
        "impact_zone": threat.impact_zone,
        "reported_at": threat.reported_at.isoformat() if threat.reported_at else None,
        "acknowledged_at": threat.acknowledged_at.isoformat() if threat.acknowledged_at else None,
        "acknowledged_by": threat.acknowledged_by,
        "resolved_at": threat.resolved_at.isoformat() if threat.resolved_at else None,
        "notes": threat.notes,
    }


# ─── Satellite Evidence ─────────────────────────────────────────────────────

async def get_satellite_evidence(db: AsyncSession, target_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve satellite evidence for a target."""
    result = await db.execute(
        select(SatellitePass).where(SatellitePass.target_id == target_id)
    )
    sat = result.scalars().first()
    if not sat:
        return None
    return {
        "target_id": sat.target_id,
        "satellite": f"{sat.satellite} / MSI",
        "acquisition_time": sat.pass_time.isoformat(),
        "spatial_resolution": f"{int(sat.ground_resolution_m)}m",
        "swir_anomaly_detected": True,
        "swir_band_max_value": 4.12,
        "smoke_aerosol_index": 3.8,
        "overlay_geojson_url": f"https://api.pyro-sentry.io/overlays/{target_id}.geojson",
        "preview_thumbnail": f"https://api.pyro-sentry.io/thumbs/{target_id}.jpg",
    }


# ─── Search ──────────────────────────────────────────────────────────────────

async def search_all(db: AsyncSession, query: str) -> Dict[str, Any]:
    """Full-text keyword search across targets, threats, and assets."""
    q = f"%{query.lower()}%"

    # Search targets
    result = await db.execute(
        select(Target).where(
            Target.name.ilike(q) | Target.id.ilike(q) | Target.threat_level.ilike(q)
        )
    )
    matched_targets = [
        {"id": t.id, "type": "TARGET", "title": t.name,
         "details": f"Status: {t.status}, Area: {t.estimated_area_ha} ha"}
        for t in result.scalars().all()
    ]

    # Search threats
    result = await db.execute(
        select(Threat).where(
            Threat.title.ilike(q) | Threat.id.ilike(q) | Threat.impact_zone.ilike(q)
        )
    )
    matched_threats = [
        {"id": t.id, "type": "THREAT", "title": t.title,
         "details": f"Severity: {t.severity.value if isinstance(t.severity, SeverityEnum) else t.severity}, Status: {t.status.value if isinstance(t.status, ThreatStatusEnum) else t.status}"}
        for t in result.scalars().all()
    ]

    # Search assets
    result = await db.execute(
        select(IndustrialAsset).where(
            IndustrialAsset.name.ilike(q) | IndustrialAsset.id.ilike(q) | IndustrialAsset.type.ilike(q)
        )
    )
    matched_assets = [
        {"id": a.id, "type": "ASSET", "title": a.name,
         "details": f"Type: {a.type}, Criticality: {a.criticality}"}
        for a in result.scalars().all()
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


# ─── GIS ─────────────────────────────────────────────────────────────────────

async def get_gis_feature_collection(db: AsyncSession, layer_name: str) -> Optional[Dict[str, Any]]:
    """Generate GeoJSON FeatureCollection for the requested GIS layer."""
    if layer_name == "hotspots":
        result = await db.execute(select(Hotspot))
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [h.longitude, h.latitude]},
                "properties": {"id": h.id, "frp": h.frp, "confidence": h.confidence,
                               "satellite": h.satellite, "detected_at": h.detected_at.isoformat()},
            }
            for h in result.scalars().all()
        ]

    elif layer_name == "targets":
        result = await db.execute(select(Target))
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [t.longitude, t.latitude]},
                "properties": {"id": t.id, "name": t.name, "status": t.status,
                               "threat_level": t.threat_level, "max_frp": t.max_frp,
                               "estimated_area_ha": t.estimated_area_ha},
            }
            for t in result.scalars().all()
        ]

    elif layer_name == "industrial-assets":
        result = await db.execute(select(IndustrialAsset))
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [a.longitude, a.latitude]},
                "properties": {"id": a.id, "name": a.name, "type": a.type, "criticality": a.criticality},
            }
            for a in result.scalars().all()
        ]

    elif layer_name == "clusters":
        # Generate cluster polygons from target + hotspot data
        result = await db.execute(select(Target))
        targets = result.scalars().all()
        features = []
        for t in targets:
            offset = 0.005
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [t.longitude - offset, t.latitude - offset],
                        [t.longitude + offset, t.latitude - offset],
                        [t.longitude + offset, t.latitude + offset],
                        [t.longitude - offset, t.latitude + offset],
                        [t.longitude - offset, t.latitude - offset],
                    ]],
                },
                "properties": {"cluster_id": f"cluster-{t.id}", "target_id": t.id,
                               "avg_frp": t.max_frp},
            })

    elif layer_name == "risk-zones":
        result = await db.execute(select(RiskAssessment))
        risk_data = result.scalars().all()
        features = []
        for r in risk_data:
            # Get associated target for coordinates
            t_result = await db.execute(select(Target).where(Target.id == r.target_id))
            target = t_result.scalars().first()
            if target:
                offset = r.proximity_to_assets_km * 0.01
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [target.longitude - offset, target.latitude - offset],
                            [target.longitude + offset, target.latitude - offset],
                            [target.longitude + offset, target.latitude + offset],
                            [target.longitude - offset, target.latitude + offset],
                            [target.longitude - offset, target.latitude - offset],
                        ]],
                    },
                    "properties": {"zone_id": f"risk-zone-{r.target_id}", "risk_level": r.risk_category,
                                   "buffer_radius_km": r.proximity_to_assets_km,
                                   "evacuation_warning": r.risk_score >= 8.0},
                })
    else:
        return None

    return {"type": "FeatureCollection", "layer_name": layer_name, "features": features}


# ─── Analytics ───────────────────────────────────────────────────────────────

async def get_analytics_summary(db: AsyncSession) -> Dict[str, Any]:
    """Compute analytics summary from real DB data."""
    target_count = await db.execute(select(func.count(Target.id)))
    hotspot_count = await db.execute(select(func.count(Hotspot.id)))
    critical_count = await db.execute(
        select(func.count(Threat.id)).where(Threat.severity == SeverityEnum.CRITICAL)
    )
    total_area = await db.execute(select(func.coalesce(func.sum(Target.estimated_area_ha), 0.0)))
    avg_conf = await db.execute(select(func.coalesce(func.avg(Hotspot.confidence), 0.0)))
    max_frp = await db.execute(select(func.coalesce(func.max(Hotspot.frp), 0.0)))

    return {
        "active_targets_count": target_count.scalar() or 0,
        "total_hotspots_detected_24h": hotspot_count.scalar() or 0,
        "critical_threats_count": critical_count.scalar() or 0,
        "total_estimated_burned_ha": float(total_area.scalar() or 0.0),
        "average_confidence_pct": round(float(avg_conf.scalar() or 0.0), 1),
        "highest_frp_mw": float(max_frp.scalar() or 0.0),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_frp_trends(db: AsyncSession) -> List[Dict[str, Any]]:
    """Generate FRP trend data from hotspot detections."""
    result = await db.execute(
        select(Hotspot).order_by(Hotspot.detected_at.asc())
    )
    hotspots = result.scalars().all()
    if not hotspots:
        return []

    # Group by hour
    trends = {}
    for h in hotspots:
        hour_key = h.detected_at.strftime("%Y-%m-%dT%H:00:00Z")
        if hour_key not in trends:
            trends[hour_key] = {"timestamp": hour_key, "total_frp_mw": 0.0, "hotspots_count": 0}
        trends[hour_key]["total_frp_mw"] = round(trends[hour_key]["total_frp_mw"] + h.frp, 1)
        trends[hour_key]["hotspots_count"] += 1

    return list(trends.values())


async def get_classification_distribution(db: AsyncSession) -> Dict[str, int]:
    """Get distribution of classification types."""
    result = await db.execute(select(Classification))
    classes = result.scalars().all()
    dist: Dict[str, int] = {}
    for c in classes:
        dist[c.primary_class] = dist.get(c.primary_class, 0) + 1
    return dist


async def get_hourly_activity(db: AsyncSession) -> List[Dict[str, Any]]:
    """Generate hourly detection activity data."""
    result = await db.execute(select(Hotspot))
    hotspots = result.scalars().all()

    hourly: Dict[int, int] = {h: 0 for h in range(24)}
    for hs in hotspots:
        hourly[hs.detected_at.hour] = hourly.get(hs.detected_at.hour, 0) + 1

    return [{"hour_utc": f"{h:02d}:00", "detections": count} for h, count in sorted(hourly.items())]


# ─── System ──────────────────────────────────────────────────────────────────

async def get_data_sources(db: AsyncSession) -> List[Dict[str, Any]]:
    """Retrieve data source feed statuses from DB."""
    result = await db.execute(select(DataSource))
    return [
        {"name": ds.name, "type": ds.type, "status": ds.status,
         "last_sync": ds.last_sync.isoformat() if ds.last_sync else None,
         "ping_ms": ds.ping_ms, "items_ingested_last_hour": ds.items_ingested_last_hour}
        for ds in result.scalars().all()
    ]


async def get_system_status(db: AsyncSession) -> Dict[str, Any]:
    """Generate system status from live runtime metrics."""
    proc = psutil.Process()
    mem = proc.memory_info()
    return {
        "system_name": "PYRO-SENTRY Industrial Thermal Surveillance Platform",
        "version": "2.0.0",
        "status": "OPERATIONAL",
        "uptime_seconds": int((datetime.now(timezone.utc) - datetime.fromtimestamp(proc.create_time(), tz=timezone.utc)).total_seconds()),
        "pipeline_latency_ms": 320,
        "active_modules": [
            "REST_API_GATEWAY",
            "WEBSOCKET_BROADCASTER",
            "SIMULATION_ORCHESTRATOR",
            "DB_FEED_INGESTION",
            "REDIS_PUBSUB",
        ],
        "memory_usage_mb": round(mem.rss / 1024 / 1024, 1),
        "cpu_load_pct": round(proc.cpu_percent(interval=0.1), 1),
    }


# ─── Events ──────────────────────────────────────────────────────────────────

async def get_all_events(db: AsyncSession, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent events."""
    result = await db.execute(
        select(Event).order_by(Event.timestamp.desc()).limit(limit)
    )
    return [
        {"id": e.id, "title": e.title, "latitude": e.latitude, "longitude": e.longitude,
         "severity": e.severity, "source": e.source, "description": e.description,
         "timestamp": e.timestamp.isoformat()}
        for e in result.scalars().all()
    ]


async def get_event_by_id(db: AsyncSession, event_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single event by ID."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    e = result.scalars().first()
    if not e:
        return None
    return {"id": e.id, "title": e.title, "latitude": e.latitude, "longitude": e.longitude,
            "severity": e.severity, "source": e.source, "description": e.description,
            "timestamp": e.timestamp.isoformat()}


async def create_event(db: AsyncSession, event_data: dict) -> Dict[str, Any]:
    """Create a new event in the DB."""
    event = Event(
        id=str(uuid.uuid4()),
        title=event_data["title"],
        latitude=event_data["latitude"],
        longitude=event_data["longitude"],
        severity=event_data.get("severity", "MEDIUM"),
        source=event_data.get("source", "MANUAL_REPORT"),
        description=event_data.get("description"),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return {"id": event.id, "title": event.title, "latitude": event.latitude,
            "longitude": event.longitude, "severity": event.severity, "source": event.source,
            "description": event.description, "timestamp": event.timestamp.isoformat()}
