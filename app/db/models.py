"""
PYRO-SENTRY Database Models.

All SQLAlchemy ORM models for the industrial thermal surveillance platform.
Threat status uses the PRD lifecycle: NEW → ACKNOWLEDGED → INVESTIGATING → DISPATCHED → RESOLVED (+ FALSE_POSITIVE).
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Boolean, Integer, Text, DateTime,
    ForeignKey, Enum, JSON, Index,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


# ─── Enums ───────────────────────────────────────────────────────────────────

class ThreatStatusEnum(str, enum.Enum):
    """PRD-compliant threat lifecycle states."""
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    DISPATCHED = "DISPATCHED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class UserRole(str, enum.Enum):
    """RBAC roles for the platform."""
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class SeverityEnum(str, enum.Enum):
    """Severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ─── Helper ──────────────────────────────────────────────────────────────────

def _utcnow():
    return datetime.now(timezone.utc)


# ─── Auth Models ─────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")


# ─── Domain Models ───────────────────────────────────────────────────────────

class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(String(36), primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    frp = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    satellite = Column(String(100), nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    target_id = Column(String(36), ForeignKey("targets.id", ondelete="SET NULL"), nullable=True, index=True)

    target = relationship("Target", back_populates="hotspots")

    __table_args__ = (
        Index("ix_hotspots_frp", "frp"),
        Index("ix_hotspots_confidence", "confidence"),
    )


class Target(Base):
    __tablename__ = "targets"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    estimated_area_ha = Column(Float, nullable=False, default=0.0)
    max_frp = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    first_detected = Column(DateTime(timezone=True), nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=False)
    threat_level = Column(String(50), nullable=False, default="LOW")

    # Relationships
    hotspots = relationship("Hotspot", back_populates="target")
    observations = relationship("Observation", back_populates="target", cascade="all, delete-orphan")
    history = relationship("TargetHistory", back_populates="target", cascade="all, delete-orphan")
    classification = relationship("Classification", back_populates="target", uselist=False, cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="target", uselist=False, cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="target", uselist=False, cascade="all, delete-orphan")
    satellite_pass = relationship("SatellitePass", back_populates="target", uselist=False, cascade="all, delete-orphan")
    threats = relationship("Threat", back_populates="target")

    __table_args__ = (
        Index("ix_targets_status", "status"),
        Index("ix_targets_threat_level", "threat_level"),
    )


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String(36), primary_key=True)
    target_id = Column(String(36), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    sensor = Column(String(100), nullable=False)
    frp = Column(Float, nullable=False)
    brightness_temp_k = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)

    target = relationship("Target", back_populates="observations")


class TargetHistory(Base):
    __tablename__ = "target_history"

    id = Column(String(36), primary_key=True)
    target_id = Column(String(36), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    event = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    details = Column(Text, nullable=True)

    target = relationship("Target", back_populates="history")


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(String(36), primary_key=True)
    target_id = Column(String(36), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    primary_class = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities = Column(JSON, nullable=False)
    model_version = Column(String(50), nullable=False)
    evaluated_at = Column(DateTime(timezone=True), nullable=False)

    target = relationship("Target", back_populates="classification")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True)
    target_id = Column(String(36), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    risk_score = Column(Float, nullable=False)
    risk_category = Column(String(50), nullable=False)
    proximity_to_assets_km = Column(Float, nullable=False)
    threatened_assets = Column(JSON, nullable=False, default=list)
    wind_speed_kmh = Column(Float, nullable=False)
    wind_direction = Column(String(10), nullable=False)
    rate_of_spread_m_min = Column(Float, nullable=False)

    target = relationship("Target", back_populates="risk_assessment")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True)
    target_id = Column(String(36), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    evidence_count = Column(Integer, nullable=False, default=0)
    items = Column(JSON, nullable=False, default=list)

    target = relationship("Target", back_populates="evidence")


class SatellitePass(Base):
    __tablename__ = "satellite_passes"

    id = Column(String(36), primary_key=True)
    target_id = Column(String(36), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    satellite = Column(String(100), nullable=False)
    pass_time = Column(DateTime(timezone=True), nullable=False)
    cloud_cover_pct = Column(Float, nullable=False)
    bands_available = Column(JSON, nullable=False, default=list)
    image_url = Column(String(500), nullable=False)
    ground_resolution_m = Column(Float, nullable=False)

    target = relationship("Target", back_populates="satellite_pass")


class Threat(Base):
    __tablename__ = "threats"

    id = Column(String(36), primary_key=True)
    target_id = Column(String(36), ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(Enum(SeverityEnum), nullable=False, default=SeverityEnum.MEDIUM)
    status = Column(Enum(ThreatStatusEnum), nullable=False, default=ThreatStatusEnum.NEW)
    risk_score = Column(Float, nullable=False)
    impact_zone = Column(String(255), nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    target = relationship("Target", back_populates="threats")

    __table_args__ = (
        Index("ix_threats_status", "status"),
        Index("ix_threats_severity", "severity"),
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(String(50), nullable=False, default="MEDIUM")
    source = Column(String(100), nullable=False, default="MANUAL_REPORT")
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class IndustrialAsset(Base):
    __tablename__ = "industrial_assets"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    criticality = Column(String(50), nullable=False)


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="ONLINE")
    last_sync = Column(DateTime(timezone=True), nullable=True)
    ping_ms = Column(Integer, nullable=True)
    items_ingested_last_hour = Column(Integer, nullable=True, default=0)
