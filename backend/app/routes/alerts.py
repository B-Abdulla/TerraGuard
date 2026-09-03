"""Alert routes: list alerts, send targeted alerts, test SMS."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth import get_current_user, require_roles
from app.models import User, Alert, UserRole, RiskZone
from app.schemas import AlertResponse, TestSmsRequest
from app.services.alert_service import alert_service
from app.services.spatial_service import find_affected_users
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


@router.get("")
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in (UserRole.AUTHORITY, UserRole.ADMIN, UserRole.RESPONSE_TEAM):
        result = await db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(200))
    else:
        result = await db.execute(
            select(Alert).where(Alert.user_id == current_user.id).order_by(Alert.created_at.desc())
        )
    alerts = result.scalars().all()
    return {
        "alerts": [
            {
                "id": str(a.id), "user_id": str(a.user_id), "phone_number": a.phone_number,
                "risk_zone_id": str(a.risk_zone_id) if a.risk_zone_id else None,
                "risk_score": a.risk_score, "risk_level": a.risk_level.value,
                "message": a.message, "status": a.status.value,
                "twilio_sid": a.twilio_sid, "error_info": a.error_info,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "sent_at": a.sent_at.isoformat() if a.sent_at else None,
            }
            for a in alerts
        ],
        "count": len(alerts),
    }


@router.get("/{alert_id}")
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": str(alert.id), "user_id": str(alert.user_id), "phone_number": alert.phone_number,
        "risk_zone_id": str(alert.risk_zone_id) if alert.risk_zone_id else None,
        "risk_score": alert.risk_score, "risk_level": alert.risk_level.value,
        "message": alert.message, "status": alert.status.value,
        "twilio_sid": alert.twilio_sid, "error_info": alert.error_info,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "sent_at": alert.sent_at.isoformat() if alert.sent_at else None,
    }


@router.post("/send/{zone_id}")
async def send_targeted_alerts(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    """Send alerts to all users inside a risk zone."""
    result = await db.execute(select(RiskZone).where(RiskZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Risk zone not found")

    affected_users = await find_affected_users(db, zone_id)
    if not affected_users:
        return {"message": "No affected users found in this zone", "alerts_sent": 0}

    alerts_sent = []
    for user in affected_users:
        alert = await alert_service.send_alert(
            db=db,
            user_id=str(user.id),
            phone_number=user.phone_number,
            risk_score=zone.risk_score,
            risk_level=zone.risk_level.value,
            risk_zone_id=zone_id,
            location_name=zone.name,
        )
        alerts_sent.append({
            "alert_id": str(alert.id),
            "user": user.full_name,
            "phone": user.phone_number,
            "status": alert.status.value,
        })

    await log_event(db, "ALERTS_SENT", f"Targeted alerts sent for zone {zone.name}",
                    severity="WARNING",
                    metadata={"zone_id": zone_id, "count": len(alerts_sent)})

    return {
        "message": f"Alerts sent to {len(alerts_sent)} affected users",
        "alerts_sent": len(alerts_sent),
        "details": alerts_sent,
    }


@router.post("/test-sms")
async def test_sms(
    data: TestSmsRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    result = await alert_service.send_test_sms(data.phone_number, data.message)
    return result
