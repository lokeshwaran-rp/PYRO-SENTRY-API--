"""
Seed data for PYRO-SENTRY — industrial/multi-category domain.
Replaces the old wildfire-only mock data with realistic industrial thermal surveillance data.
"""

import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import (
    Hotspot, Target, Observation, TargetHistory, Classification,
    RiskAssessment, Evidence, SatellitePass, Threat, Event,
    IndustrialAsset, DataSource, ThreatStatusEnum, SeverityEnum,
)


def _ts(hours_ago: float = 0) -> datetime:
    """Generate a UTC timestamp `hours_ago` in the past."""
    return datetime.now(timezone.utc) - timedelta(hours=hours_ago)


async def seed_database(session: AsyncSession) -> None:
    """
    Populate database with industrial thermal surveillance seed data.
    Only seeds if the targets table is empty (idempotent).
    """
    result = await session.execute(select(Target).limit(1))
    if result.scalars().first() is not None:
        return  # Already seeded

    # ─── Targets ─────────────────────────────────────────────────────────
    tgt_001 = Target(
        id="tgt-001",
        name="Refinery Complex Alpha — Thermal Cluster",
        status="ACTIVE",
        latitude=29.7150,
        longitude=-95.0792,
        estimated_area_ha=48.6,
        max_frp=124.5,
        confidence_score=0.94,
        first_detected=_ts(6.0),
        last_updated=_ts(0.5),
        threat_level="HIGH",
    )
    tgt_002 = Target(
        id="tgt-002",
        name="Pipeline Corridor B12 — Anomaly",
        status="MONITORING",
        latitude=30.2672,
        longitude=-97.7431,
        estimated_area_ha=12.0,
        max_frp=45.0,
        confidence_score=0.81,
        first_detected=_ts(4.0),
        last_updated=_ts(1.0),
        threat_level="MEDIUM",
    )
    tgt_003 = Target(
        id="tgt-003",
        name="Solar Farm Delta — Reflection Artifact",
        status="MONITORING",
        latitude=32.7157,
        longitude=-117.1611,
        estimated_area_ha=3.5,
        max_frp=8.2,
        confidence_score=0.42,
        first_detected=_ts(2.0),
        last_updated=_ts(0.5),
        threat_level="LOW",
    )
    session.add_all([tgt_001, tgt_002, tgt_003])

    # ─── Hotspots ────────────────────────────────────────────────────────
    session.add_all([
        Hotspot(id="hs-101", latitude=29.7155, longitude=-95.0790, frp=124.5, confidence=92.0,
                satellite="MODIS_Terra", detected_at=_ts(4.0), target_id="tgt-001"),
        Hotspot(id="hs-102", latitude=29.7148, longitude=-95.0795, frp=88.2, confidence=85.0,
                satellite="VIIRS_NOAA20", detected_at=_ts(3.5), target_id="tgt-001"),
        Hotspot(id="hs-103", latitude=30.2675, longitude=-97.7435, frp=45.0, confidence=78.0,
                satellite="VIIRS_SuomiNPP", detected_at=_ts(2.0), target_id="tgt-002"),
        Hotspot(id="hs-104", latitude=32.7160, longitude=-117.1615, frp=8.2, confidence=35.0,
                satellite="GOES-16", detected_at=_ts(1.0), target_id="tgt-003"),
    ])

    # ─── Observations ────────────────────────────────────────────────────
    session.add_all([
        Observation(id="obs-901", target_id="tgt-001", timestamp=_ts(6.0), sensor="VIIRS",
                    frp=65.4, brightness_temp_k=342.1, confidence=88.0),
        Observation(id="obs-902", target_id="tgt-001", timestamp=_ts(3.5), sensor="MODIS",
                    frp=124.5, brightness_temp_k=389.4, confidence=95.0),
        Observation(id="obs-903", target_id="tgt-002", timestamp=_ts(2.0), sensor="VIIRS_SuomiNPP",
                    frp=45.0, brightness_temp_k=325.0, confidence=78.0),
    ])

    # ─── History ─────────────────────────────────────────────────────────
    session.add_all([
        TargetHistory(id=str(uuid.uuid4()), target_id="tgt-001", event="TARGET_DETECTED",
                      timestamp=_ts(6.0), details="Initial cluster of 2 thermal detections near refinery complex."),
        TargetHistory(id=str(uuid.uuid4()), target_id="tgt-001", event="THREAT_ESCALATION",
                      timestamp=_ts(3.0), details="FRP exceeded 100 MW threshold. Threat level elevated to HIGH."),
        TargetHistory(id=str(uuid.uuid4()), target_id="tgt-002", event="TARGET_DETECTED",
                      timestamp=_ts(4.0), details="Thermal anomaly detected along pipeline corridor."),
    ])

    # ─── Classifications ─────────────────────────────────────────────────
    session.add_all([
        Classification(id=str(uuid.uuid4()), target_id="tgt-001", primary_class="INDUSTRIAL_FLARE",
                       confidence=0.72, probabilities={"INDUSTRIAL_FLARE": 0.72, "WILDFIRE": 0.18, "PRESCRIBED_BURN": 0.06, "FALSE_POSITIVE": 0.04},
                       model_version="v3.1-resnet", evaluated_at=_ts(2.0)),
        Classification(id=str(uuid.uuid4()), target_id="tgt-002", primary_class="PRESCRIBED_BURN",
                       confidence=0.65, probabilities={"WILDFIRE": 0.25, "PRESCRIBED_BURN": 0.65, "INDUSTRIAL_FLARE": 0.05, "FALSE_POSITIVE": 0.05},
                       model_version="v3.1-resnet", evaluated_at=_ts(1.5)),
        Classification(id=str(uuid.uuid4()), target_id="tgt-003", primary_class="FALSE_POSITIVE",
                       confidence=0.88, probabilities={"WILDFIRE": 0.03, "PRESCRIBED_BURN": 0.02, "INDUSTRIAL_FLARE": 0.07, "FALSE_POSITIVE": 0.88},
                       model_version="v3.1-resnet", evaluated_at=_ts(0.5)),
    ])

    # ─── Risk Assessments ────────────────────────────────────────────────
    session.add_all([
        RiskAssessment(id=str(uuid.uuid4()), target_id="tgt-001", risk_score=8.7, risk_category="CRITICAL",
                       proximity_to_assets_km=0.3, threatened_assets=["Refinery Unit 4A", "LNG Storage Tank Farm"],
                       wind_speed_kmh=28.0, wind_direction="NE", rate_of_spread_m_min=14.5),
        RiskAssessment(id=str(uuid.uuid4()), target_id="tgt-002", risk_score=4.2, risk_category="MODERATE",
                       proximity_to_assets_km=5.4, threatened_assets=["Pipeline Junction B12"],
                       wind_speed_kmh=12.0, wind_direction="SW", rate_of_spread_m_min=4.1),
        RiskAssessment(id=str(uuid.uuid4()), target_id="tgt-003", risk_score=1.2, risk_category="LOW",
                       proximity_to_assets_km=15.0, threatened_assets=[],
                       wind_speed_kmh=5.0, wind_direction="N", rate_of_spread_m_min=0.0),
    ])

    # ─── Evidence ────────────────────────────────────────────────────────
    session.add_all([
        Evidence(id=str(uuid.uuid4()), target_id="tgt-001", evidence_count=4, items=[
            {"type": "THERMAL_ANOMALY", "sensor": "VIIRS I-Band", "value": "389.4 K", "weight": 0.4},
            {"type": "HYDROCARBON_PLUME", "sensor": "Sentinel-2 SWIR", "value": "Visible SWIR plume", "weight": 0.3},
            {"type": "PROXIMITY_TO_FACILITY", "source": "Asset Registry", "value": "0.3 km to Refinery Unit 4A", "weight": 0.2},
            {"type": "WIND_RISK", "source": "Weather Station Gulf-7", "value": "28 km/h NE", "weight": 0.1},
        ]),
        Evidence(id=str(uuid.uuid4()), target_id="tgt-002", evidence_count=2, items=[
            {"type": "THERMAL_ANOMALY", "sensor": "VIIRS", "value": "325 K", "weight": 0.6},
            {"type": "PERMIT_MATCH", "source": "Land Use DB", "value": "Agricultural clearance permit active", "weight": 0.4},
        ]),
    ])

    # ─── Satellite Passes ────────────────────────────────────────────────
    session.add_all([
        SatellitePass(id=str(uuid.uuid4()), target_id="tgt-001", satellite="Sentinel-2B",
                      pass_time=_ts(3.0), cloud_cover_pct=2.1,
                      bands_available=["B02_BLUE", "B03_GREEN", "B04_RED", "B08_NIR", "B12_SWIR"],
                      image_url="https://imagery.pyro-sentry.io/passes/tgt-001-sentinel2-swir.tif",
                      ground_resolution_m=10.0),
        SatellitePass(id=str(uuid.uuid4()), target_id="tgt-002", satellite="Landsat-9",
                      pass_time=_ts(2.5), cloud_cover_pct=5.0,
                      bands_available=["B4_RED", "B5_NIR", "B7_SWIR2"],
                      image_url="https://imagery.pyro-sentry.io/passes/tgt-002-landsat9.tif",
                      ground_resolution_m=30.0),
    ])

    # ─── Threats ─────────────────────────────────────────────────────────
    session.add_all([
        Threat(id="threat-501", target_id="tgt-001", title="Unplanned Flare Escalation — Refinery Alpha",
               severity=SeverityEnum.CRITICAL, status=ThreatStatusEnum.NEW, risk_score=8.7,
               impact_zone="Houston Ship Channel — Industrial Corridor", reported_at=_ts(3.0),
               notes="Abnormal flare intensity detected. Potential process upset."),
        Threat(id="threat-502", target_id="tgt-002", title="Pipeline Thermal Anomaly — Corridor B12",
               severity=SeverityEnum.MEDIUM, status=ThreatStatusEnum.ACKNOWLEDGED, risk_score=4.2,
               impact_zone="Central Texas Pipeline Network", reported_at=_ts(2.0),
               acknowledged_at=_ts(1.5), acknowledged_by="Operator_08",
               notes="Field crew dispatched for inspection."),
    ])

    # ─── Events (Alerts) ────────────────────────────────────────────────
    session.add_all([
        Event(id="evt-001", title="Refinery Alpha — Thermal Spike Alert",
              latitude=29.7150, longitude=-95.0792, severity="HIGH",
              source="SATELLITE_THERMAL_ALERT",
              description="Significant thermal anomaly detected near refinery complex.",
              timestamp=_ts(3.0)),
    ])

    # ─── Industrial Assets ───────────────────────────────────────────────
    session.add_all([
        IndustrialAsset(id="asset-01", name="Refinery Unit 4A — Distillation Tower",
                        type="REFINERY", latitude=29.7160, longitude=-95.0780, criticality="CRITICAL"),
        IndustrialAsset(id="asset-02", name="LNG Storage Tank Farm",
                        type="GAS_STORAGE", latitude=29.7180, longitude=-95.0760, criticality="CRITICAL"),
        IndustrialAsset(id="asset-03", name="Pipeline Junction B12",
                        type="PIPELINE", latitude=30.2680, longitude=-97.7440, criticality="HIGH"),
        IndustrialAsset(id="asset-04", name="Solar Farm Delta — Array C",
                        type="POWER_GENERATION", latitude=32.7165, longitude=-117.1620, criticality="MEDIUM"),
        IndustrialAsset(id="asset-05", name="Gulf Coast Compressor Station #7",
                        type="GAS_COMPRESSION", latitude=29.3890, longitude=-94.9020, criticality="HIGH"),
    ])

    # ─── Data Sources ────────────────────────────────────────────────────
    session.add_all([
        DataSource(id=str(uuid.uuid4()), name="NASA FIRMS (MODIS/VIIRS)",
                   type="THERMAL_HOTSPOT_FEED", status="ONLINE",
                   last_sync=_ts(0.1), ping_ms=142, items_ingested_last_hour=14),
        DataSource(id=str(uuid.uuid4()), name="NOAA GOES-East / GOES-West",
                   type="GEOSTATIONARY_FIRE_FEED", status="ONLINE",
                   last_sync=_ts(0.05), ping_ms=89, items_ingested_last_hour=52),
        DataSource(id=str(uuid.uuid4()), name="Copernicus Sentinel-2 Hub",
                   type="HIGH_RES_OPTICAL_FEED", status="ONLINE",
                   last_sync=_ts(0.5), ping_ms=310, items_ingested_last_hour=2),
        DataSource(id=str(uuid.uuid4()), name="NOAA National Weather Service",
                   type="METEOROLOGY_FEED", status="ONLINE",
                   last_sync=_ts(0.2), ping_ms=65, items_ingested_last_hour=120),
    ])

    await session.commit()
