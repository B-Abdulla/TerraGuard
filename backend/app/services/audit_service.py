"""Audit logging service – records important system events."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import SystemEvent


async def log_event(
    db: AsyncSession,
    event_type: str,
    description: str,
    severity: str = "INFO",
    metadata: Optional[Dict[str, Any]] = None,
):
    """Persist a system event for audit trail."""
    event = SystemEvent(
        id=uuid.uuid4(),
        event_type=event_type,
        severity=severity,
        description=description,
        metadata_=metadata or {},
        created_at=datetime.utcnow(),
    )
    db.add(event)
    await db.flush()
    return event
