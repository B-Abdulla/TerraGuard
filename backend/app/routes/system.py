"""System health, data sources, Twilio status, audit log, and demo scenario routes."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth import get_current_user, require_roles
from app.config import get_settings
from app.models import (
    User, UserRole, DataSource, SystemEvent, RiskZone, Alert, RiskLevel,
    WeatherData, RainfallData, RiskPrediction,
)
from app.schemas import DemoScenarioRequest
from app.services.ai_service import ai_service
from app.services.risk_engine import risk_engine
from app.services.alert_service import alert_service
from app.services.spatial_service import create_risk_zone, find_affected_users
from app.services.audit_service import log_event

settings = get_settings()
router = APIRouter(prefix="/api/v1/system", tags=["System"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    # Database check
    db_status = "AVAILABLE"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "ERROR"

    # AI check
    ai_status_val = "AVAILABLE" if ai_service.model is not None else "UNAVAILABLE"

    # Twilio check
    twilio_status = alert_service.get_twilio_status()

    return {
        "database": db_status,
        "ai_model": ai_status_val,
        "weather_source": "DEMO" if settings.DEMO_MODE else ("AVAILABLE" if settings.WEATHER_API_KEY else "UNAVAILABLE"),
        "rainfall_source": "DEMO" if settings.DEMO_MODE else "UNAVAILABLE",
        "satellite_data": "DEMO" if settings.DEMO_MODE else "UNAVAILABLE",
        "twilio": twilio_status["status"],
        "gis": "AVAILABLE",
        "demo_mode": settings.DEMO_MODE,
    }


@router.get("/data-sources")
async def data_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataSource))
    sources = result.scalars().all()
    return {
        "sources": [
            {
                "name": s.name, "source_type": s.source_type, "status": s.status.value,
                "last_successful_update": s.last_successful_update.isoformat() if s.last_successful_update else None,
                "error_info": s.error_info,
            }
            for s in sources
        ]
    }


@router.get("/twilio")
async def twilio_status():
    return alert_service.get_twilio_status()


@router.get("/events")
async def system_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.AUTHORITY)),
):
    result = await db.execute(
        select(SystemEvent).order_by(SystemEvent.created_at.desc()).limit(200)
    )
    events = result.scalars().all()
    return {
        "events": [
            {
                "id": str(e.id), "event_type": e.event_type, "severity": e.severity,
                "description": e.description, "metadata": e.metadata_,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
        "count": len(events),
    }


@router.get("/stats")
async def system_stats(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    from app.models import CommunityReport

    users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    zones_count = (await db.execute(select(func.count(RiskZone.id)).where(RiskZone.is_active == True))).scalar() or 0
    alerts_count = (await db.execute(select(func.count(Alert.id)))).scalar() or 0
    reports_count = (await db.execute(select(func.count(CommunityReport.id)))).scalar() or 0

    # Critical zones
    critical_count = (await db.execute(
        select(func.count(RiskZone.id)).where(RiskZone.is_active == True, RiskZone.risk_level == RiskLevel.CRITICAL)
    )).scalar() or 0
    high_count = (await db.execute(
        select(func.count(RiskZone.id)).where(RiskZone.is_active == True, RiskZone.risk_level == RiskLevel.HIGH)
    )).scalar() or 0

    return {
        "total_users": users_count,
        "active_risk_zones": zones_count,
        "critical_zones": critical_count,
        "high_risk_zones": high_count,
        "total_alerts": alerts_count,
        "total_reports": reports_count,
        "demo_mode": settings.DEMO_MODE,
    }


# ─── Demo Scenario ──────────────────────────────────────────────────────────

@router.post("/demo-scenario")
async def run_demo_scenario(
    data: DemoScenarioRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.AUTHORITY)),
):
    """Run an end-to-end demo scenario."""
    scenarios = {
        "NORMAL": {"rainfall_24h": 10, "slope": 10, "soil_moisture": 0.2, "elevation": 300},
        "MODERATE_RAINFALL": {"rainfall_24h": 80, "slope": 20, "soil_moisture": 0.5, "elevation": 600},
        "HIGH_RISK": {"rainfall_24h": 160, "slope": 35, "soil_moisture": 0.7, "elevation": 900},
        "CRITICAL_RISK": {"rainfall_24h": 250, "slope": 45, "soil_moisture": 0.85, "elevation": 1200},
        "AI_FAILURE": None,
        "DATA_SOURCE_FAILURE": None,
        "TWILIO_DEMO": {"rainfall_24h": 200, "slope": 40, "soil_moisture": 0.8, "elevation": 1000},
    }

    if data.scenario == "AI_FAILURE":
        await log_event(db, "DEMO_SCENARIO", "AI_FAILURE scenario triggered", severity="WARNING")
        return {"scenario": data.scenario, "message": "DEMO SCENARIO: Simulated AI failure",
                "prediction": None, "risk_zone": None, "affected_users": 0, "alerts_created": 0}

    if data.scenario == "DATA_SOURCE_FAILURE":
        await log_event(db, "DEMO_SCENARIO", "DATA_SOURCE_FAILURE scenario triggered", severity="WARNING")
        return {"scenario": data.scenario, "message": "DEMO SCENARIO: Simulated data source failure",
                "prediction": None, "risk_zone": None, "affected_users": 0, "alerts_created": 0}

    env = scenarios.get(data.scenario, scenarios["NORMAL"])
    features = {
        "rainfall_1h": env.get("rainfall_24h", 10) / 24 * 3,
        "rainfall_6h": env.get("rainfall_24h", 10) / 4,
        "rainfall_24h": env.get("rainfall_24h", 10),
        "rainfall_72h": env.get("rainfall_24h", 10) * 2.5,
        "slope": env.get("slope", 10),
        "elevation": env.get("elevation", 300),
        "soil_moisture": env.get("soil_moisture", 0.3),
        "land_cover": 3,
        "historical_landslide_density": 0.5,
    }

    # 1. Predict
    try:
        result = ai_service.predict(features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {e}")

    risk_score = result["risk_score"]
    risk_level = risk_engine.classify(risk_score)

    env_factors = {}
    for key, val in features.items():
        env_factors[key] = risk_engine.classify_environmental_factor(key, val)

    # 2. Create risk zone
    lat = data.latitude or 25.57
    lng = data.longitude or 91.88
    zone = await create_risk_zone(
        db, f"Demo Zone – {data.scenario}", risk_score, risk_level.value,
        lat, lng, radius_km=5.0,
        environmental_factors=env_factors,
    )

    # 3. Find affected users
    affected = await find_affected_users(db, str(zone.id))

    # 4. Send alerts
    alerts_created = 0
    if risk_level.value in ("HIGH", "CRITICAL"):
        for user in affected:
            await alert_service.send_alert(
                db, str(user.id), user.phone_number,
                risk_score, risk_level.value, str(zone.id), zone.name,
            )
            alerts_created += 1

    await log_event(db, "DEMO_SCENARIO", f"Scenario {data.scenario} completed",
                    metadata={"risk_score": risk_score, "affected": len(affected), "alerts": alerts_created})

    return {
        "scenario": data.scenario,
        "message": f"DEMO SCENARIO: {data.scenario}",
        "prediction": {
            "risk_score": risk_score, "risk_level": risk_level.value,
            "model_version": result["model_version"],
            "environmental_factors": env_factors,
        },
        "risk_zone": {
            "id": str(zone.id), "name": zone.name,
            "center_lat": lat, "center_lng": lng,
        },
        "affected_users": len(affected),
        "alerts_created": alerts_created,
    }


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return {
        "users": [
            {
                "id": str(u.id), "full_name": u.full_name, "phone_number": u.phone_number,
                "email": u.email, "role": u.role.value, "latitude": u.latitude,
                "longitude": u.longitude, "locality": u.locality, "district": u.district,
                "state": u.state, "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "count": len(users),
    }
