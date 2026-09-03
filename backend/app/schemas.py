"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRoleEnum(str, Enum):
    RESIDENT = "RESIDENT"
    AUTHORITY = "AUTHORITY"
    RESPONSE_TEAM = "RESPONSE_TEAM"
    ADMIN = "ADMIN"


class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatusEnum(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    DEMO = "DEMO"


class ReportCategoryEnum(str, Enum):
    LANDSLIDE = "LANDSLIDE"
    ROAD_BLOCKAGE = "ROAD_BLOCKAGE"
    HEAVY_RAINFALL = "HEAVY_RAINFALL"
    GROUND_CRACK = "GROUND_CRACK"
    FLOODING = "FLOODING"
    OTHER = "OTHER"


class ReportStatusEnum(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: UserRoleEnum = UserRoleEnum.RESIDENT
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    locality: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None


class UserLogin(BaseModel):
    phone_number: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    full_name: str
    phone_number: str
    email: Optional[str]
    role: UserRoleEnum
    latitude: Optional[float]
    longitude: Optional[float]
    locality: Optional[str]
    district: Optional[str]
    state: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Risk Prediction Schemas ────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    rainfall_1h: float = Field(0, ge=0)
    rainfall_6h: float = Field(0, ge=0)
    rainfall_24h: float = Field(0, ge=0)
    rainfall_72h: float = Field(0, ge=0)
    slope: float = Field(0, ge=0, le=90)
    elevation: float = Field(0, ge=0)
    soil_moisture: float = Field(0, ge=0, le=1)
    land_cover: int = Field(0, ge=0)
    historical_landslide_density: float = Field(0, ge=0, le=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PredictionResponse(BaseModel):
    risk_score: float
    risk_level: RiskLevelEnum
    model_version: str
    timestamp: datetime
    location: Optional[Dict[str, float]] = None
    environmental_factors: Optional[Dict[str, str]] = None


# ─── Risk Zone Schemas ──────────────────────────────────────────────────────

class RiskZoneResponse(BaseModel):
    id: str
    name: str
    risk_score: float
    risk_level: RiskLevelEnum
    model_version: Optional[str]
    center_lat: Optional[float]
    center_lng: Optional[float]
    radius_km: Optional[float]
    environmental_factors: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    geometry_geojson: Optional[Dict[str, Any]] = None
    affected_users_count: int = 0

    class Config:
        from_attributes = True


class CreateRiskZoneRequest(BaseModel):
    name: str
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: RiskLevelEnum
    center_lat: float
    center_lng: float
    radius_km: float = Field(5.0, gt=0)
    model_version: Optional[str] = "xgboost-v1"
    environmental_factors: Optional[Dict[str, Any]] = None


# ─── Alert Schemas ───────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: str
    user_id: str
    phone_number: str
    risk_zone_id: Optional[str]
    risk_score: float
    risk_level: RiskLevelEnum
    message: str
    status: AlertStatusEnum
    twilio_sid: Optional[str]
    error_info: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class TestSmsRequest(BaseModel):
    phone_number: str
    message: Optional[str] = "TERRAGUARD TEST ALERT: This is a test message."


# ─── Community Report Schemas ───────────────────────────────────────────────

class CommunityReportCreate(BaseModel):
    category: ReportCategoryEnum
    description: str = Field(..., min_length=5, max_length=2000)
    latitude: float
    longitude: float
    photo_url: Optional[str] = None


class CommunityReportResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    category: ReportCategoryEnum
    description: str
    latitude: float
    longitude: float
    photo_url: Optional[str]
    status: ReportStatusEnum
    created_at: datetime
    verifications: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class VerifyReportRequest(BaseModel):
    status: ReportStatusEnum
    notes: Optional[str] = None


# ─── Weather / Rainfall Schemas ─────────────────────────────────────────────

class WeatherResponse(BaseModel):
    id: str
    source: str
    temperature: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]
    wind_speed: Optional[float]
    description: Optional[str]
    latitude: float
    longitude: float
    recorded_at: datetime

    class Config:
        from_attributes = True


class RainfallResponse(BaseModel):
    id: str
    source: str
    rainfall_1h: float
    rainfall_6h: float
    rainfall_24h: float
    rainfall_72h: float
    cumulative_rainfall: float
    latitude: float
    longitude: float
    recorded_at: datetime

    class Config:
        from_attributes = True


# ─── System Schemas ─────────────────────────────────────────────────────────

class SystemHealthResponse(BaseModel):
    database: str
    ai_model: str
    weather_source: str
    rainfall_source: str
    satellite_data: str
    twilio: str
    gis: str
    demo_mode: bool


class DataSourceResponse(BaseModel):
    name: str
    source_type: str
    status: str
    last_successful_update: Optional[datetime]
    error_info: Optional[str]


class ModelStatusResponse(BaseModel):
    name: str
    version: str
    is_active: bool
    training_date: Optional[datetime]
    feature_schema: Optional[Dict[str, Any]]


# ─── Demo Scenario Schema ───────────────────────────────────────────────────

class DemoScenarioRequest(BaseModel):
    scenario: str = Field(..., pattern="^(NORMAL|MODERATE_RAINFALL|HIGH_RISK|CRITICAL_RISK|AI_FAILURE|DATA_SOURCE_FAILURE|TWILIO_DEMO)$")
    latitude: Optional[float] = 25.57
    longitude: Optional[float] = 91.88


class DemoScenarioResponse(BaseModel):
    scenario: str
    prediction: Optional[PredictionResponse]
    risk_zone: Optional[RiskZoneResponse]
    affected_users: int
    alerts_created: int
    message: str
