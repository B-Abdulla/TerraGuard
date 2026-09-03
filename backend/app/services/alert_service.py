"""Twilio SMS alert service with DEMO_MODE support."""

import uuid
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.models import Alert, AlertStatus, RiskLevel

settings = get_settings()


class AlertService:
    """Sends SMS alerts via Twilio or simulates them in DEMO_MODE."""

    def __init__(self):
        self._twilio_client = None

    @property
    def twilio_client(self):
        if self._twilio_client is None and not settings.DEMO_MODE:
            try:
                from twilio.rest import Client
                if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                    self._twilio_client = Client(
                        settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_AUTH_TOKEN,
                    )
            except Exception:
                pass
        return self._twilio_client

    def build_message(
        self,
        risk_level: str,
        risk_score: float,
        location_name: str = "your area",
    ) -> str:
        return (
            f"TERRAGUARD ALERT: {risk_level} landslide risk detected near {location_name}. "
            f"Risk Score: {risk_score:.2f}. "
            "Please remain alert and follow instructions from local authorities."
        )

    async def send_alert(
        self,
        db: AsyncSession,
        user_id: str,
        phone_number: str,
        risk_score: float,
        risk_level: str,
        risk_zone_id: Optional[str] = None,
        location_name: str = "your area",
    ) -> Alert:
        """Create an alert record and send (or simulate) SMS."""
        message = self.build_message(risk_level, risk_score, location_name)

        alert = Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            phone_number=phone_number,
            risk_zone_id=risk_zone_id,
            risk_score=risk_score,
            risk_level=RiskLevel(risk_level),
            message=message,
            status=AlertStatus.CREATED,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        await db.flush()

        if settings.DEMO_MODE:
            alert.status = AlertStatus.DEMO
            alert.sent_at = datetime.utcnow()
        else:
            try:
                if self.twilio_client is None:
                    raise RuntimeError("Twilio client not configured")
                tw_message = self.twilio_client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone_number,
                )
                alert.twilio_sid = tw_message.sid
                alert.status = AlertStatus.SENT
                alert.sent_at = datetime.utcnow()
            except Exception as e:
                alert.status = AlertStatus.FAILED
                alert.error_info = str(e)[:500]

        await db.flush()
        return alert

    async def send_test_sms(self, phone_number: str, message: str) -> Dict:
        """Send a one-off test SMS (or simulate in demo mode)."""
        if settings.DEMO_MODE:
            return {
                "status": "DEMO",
                "phone_number": phone_number,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "note": "DEMO MODE – SMS was not actually sent",
            }
        try:
            if self.twilio_client is None:
                raise RuntimeError("Twilio client not configured")
            tw = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number,
            )
            return {
                "status": "SENT",
                "sid": tw.sid,
                "phone_number": phone_number,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "FAILED",
                "phone_number": phone_number,
                "message": message,
                "error": str(e)[:500],
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_twilio_status(self) -> Dict:
        if settings.DEMO_MODE:
            return {"status": "DEMO", "note": "DEMO MODE – Twilio not called"}
        if self.twilio_client:
            return {"status": "AVAILABLE", "phone": settings.TWILIO_PHONE_NUMBER}
        return {"status": "UNAVAILABLE", "note": "Twilio credentials not configured"}


# Singleton
alert_service = AlertService()
