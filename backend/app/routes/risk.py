"""Risk prediction, risk zones, and AI model status routes."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.database import get_db
from app.auth import get_current_user
from app.models import User, RiskPrediction, RiskLevel, RiskZone
from app.schemas import (
    PredictionRequest, PredictionResponse, RiskZoneResponse,
    CreateRiskZoneRequest, ModelStatusResponse, RiskLevelEnum,
)
from app.services.ai_service import ai_service
from app.services.risk_engine import risk_engine
from app.services.spatial_service import (
    create_risk_zone, get_all_active_zones, find_affected_users, count_affected_users,
)
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/v1", tags=["Risk & AI"])


@router.post("/predictions/risk", response_model=PredictionResponse)
async def predict_risk(
    data: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    features = data.model_dump(exclude={"latitude", "longitude"})
    try:
        result = ai_service.predict(features)
    except Exception as e:
        await log_event(db, "AI_FAILURE", f"Prediction failed: {str(e)}", severity="ERROR")
        raise HTTPException(status_code=500, detail=f"AI model error: {str(e)}")

    risk_score = result["risk_score"]
    risk_level = risk_engine.classify(risk_score)

    # Environmental factor classification
    env_factors = {}
    for key, val in features.items():
        env_factors[key] = risk_engine.classify_environmental_factor(key, val)

    # Persist prediction
    lat = data.latitude or 25.57
    lng = data.longitude or 91.88
    prediction = RiskPrediction(
        id=uuid.uuid4(),
        risk_score=risk_score,
        risk_level=RiskLevel(risk_level.value),
        model_version=result["model_version"],
        features_used=features,
        latitude=lat,
        longitude=lng,
        location=from_shape(Point(lng, lat), srid=4326),
        created_at=datetime.utcnow(),
    )
    db.add(prediction)
    await db.flush()

    await log_event(db, "PREDICTION", f"Risk prediction: {risk_score:.4f} ({risk_level.value})",
                    metadata={"prediction_id": str(prediction.id), "risk_score": risk_score})

    return PredictionResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        model_version=result["model_version"],
        timestamp=datetime.utcnow(),
        location={"latitude": lat, "longitude": lng},
        environmental_factors=env_factors,
    )


@router.get("/risk/zones")
async def get_risk_zones(db: AsyncSession = Depends(get_db)):
    zones = await get_all_active_zones(db)
    return {"zones": zones, "count": len(zones)}


@router.post("/risk/zones", response_model=dict)
async def create_zone(
    data: CreateRiskZoneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    zone = await create_risk_zone(
        db, data.name, data.risk_score, data.risk_level.value,
        data.center_lat, data.center_lng, data.radius_km,
        data.model_version, data.environmental_factors,
    )
    user_count = await count_affected_users(db, str(zone.id))

    await log_event(db, "RISK_ZONE_CREATED", f"Zone '{data.name}' created: {data.risk_level.value}",
                    metadata={"zone_id": str(zone.id), "risk_score": data.risk_score})

    return {
        "id": str(zone.id), "name": zone.name, "risk_score": zone.risk_score,
        "risk_level": zone.risk_level.value, "affected_users": user_count,
        "message": f"Risk zone created with {user_count} affected users",
    }


@router.get("/risk/zones/{zone_id}/affected-users")
async def get_affected_users(zone_id: str, db: AsyncSession = Depends(get_db)):
    users = await find_affected_users(db, zone_id)
    return {
        "zone_id": zone_id,
        "affected_users": [
            {"id": str(u.id), "full_name": u.full_name, "phone_number": u.phone_number,
             "latitude": u.latitude, "longitude": u.longitude}
            for u in users
        ],
        "count": len(users),
    }


@router.get("/model/status")
async def model_status():
    status = ai_service.get_status()
    thresholds = risk_engine.get_thresholds()
    return {"model": status, "thresholds": thresholds}
