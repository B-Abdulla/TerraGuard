"""Spatial targeting service – PostGIS queries to find affected users."""

import uuid
import math
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID, ST_Buffer, ST_AsGeoJSON
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, Polygon
from app.models import User, RiskZone, RiskLevel


def create_circle_polygon(lat: float, lng: float, radius_km: float, num_points: int = 64) -> Polygon:
    """Create a rough circle polygon around a point (in EPSG:4326)."""
    # Approximate degrees per km at this latitude
    km_per_deg_lat = 111.32
    km_per_deg_lng = 111.32 * math.cos(math.radians(lat))
    points = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        dx = radius_km * math.cos(angle) / km_per_deg_lng
        dy = radius_km * math.sin(angle) / km_per_deg_lat
        points.append((lng + dx, lat + dy))
    points.append(points[0])
    return Polygon(points)


async def create_risk_zone(
    db: AsyncSession,
    name: str,
    risk_score: float,
    risk_level: str,
    center_lat: float,
    center_lng: float,
    radius_km: float = 5.0,
    model_version: str = "xgboost-v1",
    environmental_factors: Optional[Dict] = None,
) -> RiskZone:
    """Create a risk zone polygon in the database."""
    polygon = create_circle_polygon(center_lat, center_lng, radius_km)
    geom = from_shape(polygon, srid=4326)

    zone = RiskZone(
        id=uuid.uuid4(),
        name=name,
        risk_score=risk_score,
        risk_level=RiskLevel(risk_level),
        model_version=model_version,
        geometry=geom,
        center_lat=center_lat,
        center_lng=center_lng,
        radius_km=radius_km,
        environmental_factors=environmental_factors or {},
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(zone)
    await db.flush()
    return zone


async def find_affected_users(
    db: AsyncSession,
    zone_id: str,
    buffer_km: float = 0,
) -> List[User]:
    """Find users whose location is inside/near a risk zone."""
    # Get the risk zone geometry
    result = await db.execute(select(RiskZone).where(RiskZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        return []

    # Use ST_DWithin with a buffer (in degrees, ~0.009 per km)
    buffer_deg = buffer_km * 0.009 if buffer_km > 0 else 0

    if buffer_deg > 0:
        stmt = select(User).where(
            User.location.isnot(None),
            func.ST_DWithin(User.location, zone.geometry, buffer_deg),
        )
    else:
        stmt = select(User).where(
            User.location.isnot(None),
            func.ST_Within(User.location, zone.geometry),
        )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_affected_users(db: AsyncSession, zone_id: str) -> int:
    """Count users inside a risk zone."""
    result = await db.execute(select(RiskZone).where(RiskZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        return 0

    stmt = select(func.count(User.id)).where(
        User.location.isnot(None),
        func.ST_Within(User.location, zone.geometry),
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_zone_geojson(db: AsyncSession, zone: RiskZone) -> Dict:
    """Get GeoJSON representation of a risk zone geometry."""
    result = await db.execute(
        select(func.ST_AsGeoJSON(zone.geometry))
    )
    geojson_str = result.scalar()
    if geojson_str:
        import json
        return json.loads(geojson_str)
    return {}


async def get_all_active_zones(db: AsyncSession) -> List[Dict[str, Any]]:
    """Retrieve all active risk zones with GeoJSON and user counts."""
    result = await db.execute(
        select(RiskZone).where(RiskZone.is_active == True).order_by(RiskZone.created_at.desc())
    )
    zones = result.scalars().all()
    zone_data = []
    for zone in zones:
        geojson = await get_zone_geojson(db, zone)
        user_count = await count_affected_users(db, str(zone.id))
        zone_data.append({
            "id": str(zone.id),
            "name": zone.name,
            "risk_score": zone.risk_score,
            "risk_level": zone.risk_level.value,
            "model_version": zone.model_version,
            "center_lat": zone.center_lat,
            "center_lng": zone.center_lng,
            "radius_km": zone.radius_km,
            "environmental_factors": zone.environmental_factors,
            "is_active": zone.is_active,
            "created_at": zone.created_at.isoformat() if zone.created_at else None,
            "updated_at": zone.updated_at.isoformat() if zone.updated_at else None,
            "geometry_geojson": geojson,
            "affected_users_count": user_count,
        })
    return zone_data
