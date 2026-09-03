"""Community reports routes: create, list, verify."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.database import get_db
from app.auth import get_current_user, require_roles
from app.models import User, UserRole, CommunityReport, CommunityReportVerification, ReportStatus, ReportCategory
from app.schemas import CommunityReportCreate, CommunityReportResponse, VerifyReportRequest
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/v1/community-reports", tags=["Community Reports"])


@router.post("", status_code=201)
async def create_report(
    data: CommunityReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = CommunityReport(
        id=uuid.uuid4(),
        user_id=current_user.id,
        category=ReportCategory(data.category.value),
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        location=from_shape(Point(data.longitude, data.latitude), srid=4326),
        photo_url=data.photo_url,
        status=ReportStatus.PENDING,
        created_at=datetime.utcnow(),
    )
    db.add(report)
    await db.flush()

    await log_event(db, "COMMUNITY_REPORT", f"Report submitted: {data.category.value}",
                    metadata={"report_id": str(report.id), "user_id": str(current_user.id)})

    return {
        "id": str(report.id), "category": report.category.value,
        "description": report.description, "status": report.status.value,
        "latitude": report.latitude, "longitude": report.longitude,
        "created_at": report.created_at.isoformat(),
    }


@router.get("")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CommunityReport).order_by(CommunityReport.created_at.desc()).limit(200)
    )
    reports = result.scalars().all()
    report_list = []
    for r in reports:
        # Get verifications
        v_result = await db.execute(
            select(CommunityReportVerification).where(CommunityReportVerification.report_id == r.id)
        )
        verifications = v_result.scalars().all()

        # Get user name
        u_result = await db.execute(select(User.full_name).where(User.id == r.user_id))
        user_name = u_result.scalar() or "Unknown"

        report_list.append({
            "id": str(r.id), "user_id": str(r.user_id), "user_name": user_name,
            "category": r.category.value, "description": r.description,
            "latitude": r.latitude, "longitude": r.longitude,
            "photo_url": r.photo_url, "status": r.status.value,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "verifications": [
                {"id": str(v.id), "status": v.status.value, "notes": v.notes,
                 "verified_by": str(v.verified_by), "created_at": v.created_at.isoformat() if v.created_at else None}
                for v in verifications
            ],
        })
    return {"reports": report_list, "count": len(report_list)}


@router.get("/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CommunityReport).where(CommunityReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    v_result = await db.execute(
        select(CommunityReportVerification).where(CommunityReportVerification.report_id == report.id)
    )
    verifications = v_result.scalars().all()

    return {
        "id": str(report.id), "user_id": str(report.user_id),
        "category": report.category.value, "description": report.description,
        "latitude": report.latitude, "longitude": report.longitude,
        "photo_url": report.photo_url, "status": report.status.value,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "verifications": [
            {"id": str(v.id), "status": v.status.value, "notes": v.notes,
             "verified_by": str(v.verified_by), "created_at": v.created_at.isoformat() if v.created_at else None}
            for v in verifications
        ],
    }


@router.post("/{report_id}/verify")
async def verify_report(
    report_id: str,
    data: VerifyReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    result = await db.execute(select(CommunityReport).where(CommunityReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    verification = CommunityReportVerification(
        id=uuid.uuid4(),
        report_id=report.id,
        verified_by=current_user.id,
        status=ReportStatus(data.status.value),
        notes=data.notes,
        created_at=datetime.utcnow(),
    )
    db.add(verification)

    report.status = ReportStatus(data.status.value)
    await db.flush()

    event_type = "REPORT_VERIFIED" if data.status.value == "VERIFIED" else "REPORT_REJECTED"
    await log_event(db, event_type, f"Report {report_id} {data.status.value} by {current_user.full_name}",
                    metadata={"report_id": report_id, "verifier": str(current_user.id)})

    return {"message": f"Report {data.status.value.lower()}", "report_id": report_id, "status": data.status.value}
