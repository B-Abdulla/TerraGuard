"""All SQLAlchemy ORM models for TerraGuard."""

import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, Text, DateTime,
    ForeignKey, Enum as SAEnum, Index, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    RESIDENT = "RESIDENT"
    AUTHORITY = "AUTHORITY"
    RESPONSE_TEAM = "RESPONSE_TEAM"
    ADMIN = "ADMIN"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    DEMO = "DEMO"


class ReportCategory(str, enum.Enum):
    LANDSLIDE = "LANDSLIDE"
    ROAD_BLOCKAGE = "ROAD_BLOCKAGE"
    HEAVY_RAINFALL = "HEAVY_RAINFALL"
    GROUND_CRACK = "GROUND_CRACK"
    FLOODING = "FLOODING"
    OTHER = "OTHER"


class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class DataSourceStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    DEMO = "DEMO"


# ─── Users ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.RESIDENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # PostGIS location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geometry("POINT", srid=4326), nullable=True)
    locality = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)

    alerts = relationship("Alert", back_populates="user")
    community_reports = relationship("CommunityReport", back_populates="user")

    __table_args__ = (
        Index("idx_users_location", "location", postgresql_using="gist"),
    )


# ─── Weather / Rainfall / Satellite / Terrain ───────────────────────────────

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    description = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RainfallData(Base):
    __tablename__ = "rainfall_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)
    rainfall_1h = Column(Float, default=0)
    rainfall_6h = Column(Float, default=0)
    rainfall_24h = Column(Float, default=0)
    rainfall_72h = Column(Float, default=0)
    cumulative_rainfall = Column(Float, default=0)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SatelliteData(Base):
    __tablename__ = "satellite_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)
    ndvi = Column(Float)
    soil_moisture = Column(Float)
    land_cover = Column(Integer)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TerrainData(Base):
    __tablename__ = "terrain_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)
    elevation = Column(Float)
    slope = Column(Float)
    aspect = Column(Float)
    curvature = Column(Float)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    created_at = Column(DateTime, default=datetime.utcnow)


class HistoricalLandslide(Base):
    __tablename__ = "historical_landslides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100))
    description = Column(Text)
    severity = Column(String(50))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    occurred_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── AI / Predictions ───────────────────────────────────────────────────────

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, unique=True)
    training_date = Column(DateTime)
    feature_schema = Column(JSON)
    metadata_ = Column("metadata", JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(SAEnum(RiskLevel), nullable=False)
    model_version = Column(String(50), nullable=False)
    features_used = Column(JSON)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Risk Zones ──────────────────────────────────────────────────────────────

class RiskZone(Base):
    __tablename__ = "risk_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(SAEnum(RiskLevel), nullable=False)
    model_version = Column(String(50))
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    center_lat = Column(Float)
    center_lng = Column(Float)
    radius_km = Column(Float, default=5.0)
    environmental_factors = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_risk_zones_geometry", "geometry", postgresql_using="gist"),
    )


# ─── Alerts ──────────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    phone_number = Column(String(20), nullable=False)
    risk_zone_id = Column(UUID(as_uuid=True), ForeignKey("risk_zones.id"), nullable=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(SAEnum(RiskLevel), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(SAEnum(AlertStatus), default=AlertStatus.CREATED)
    twilio_sid = Column(String(100), nullable=True)
    error_info = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="alerts")
    risk_zone = relationship("RiskZone")


# ─── Community Reports ──────────────────────────────────────────────────────

class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category = Column(SAEnum(ReportCategory), nullable=False)
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    photo_url = Column(String(500), nullable=True)
    status = Column(SAEnum(ReportStatus), default=ReportStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="community_reports")
    verifications = relationship("CommunityReportVerification", back_populates="report")


class CommunityReportVerification(Base):
    __tablename__ = "community_report_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("community_reports.id"), nullable=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(ReportStatus), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("CommunityReport", back_populates="verifications")
    verifier = relationship("User")


# ─── System ─────────────────────────────────────────────────────────────────

class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), default="INFO")
    description = Column(Text)
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    source_type = Column(String(50), nullable=False)
    status = Column(SAEnum(DataSourceStatus), default=DataSourceStatus.UNAVAILABLE)
    last_successful_update = Column(DateTime, nullable=True)
    error_info = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
