"""Database seed script – creates demo data for Northeast India context."""

import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.database import async_session_factory, engine, Base
from app.models import (
    User, UserRole, WeatherData, RainfallData, SatelliteData, TerrainData,
    HistoricalLandslide, ModelVersion, DataSource, DataSourceStatus,
    RiskZone, RiskLevel, CommunityReport, ReportCategory, ReportStatus,
)
from app.auth import hash_password
from app.services.spatial_service import create_circle_polygon


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Check if already seeded
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        now = datetime.utcnow()

        # ── Users ────────────────────────────────────────────────────────
        # Resident A – inside Shillong risk zone
        resident_a = User(
            id=uuid.uuid4(), full_name="Bah Kynmaw Syiem", phone_number="+919876543210",
            email="bah.kynmaw@example.com", password_hash=hash_password("resident123"),
            role=UserRole.RESIDENT, latitude=25.5788, longitude=91.8933,
            location=from_shape(Point(91.8933, 25.5788), srid=4326),
            locality="Laitumkhrah", district="East Khasi Hills", state="Meghalaya",
        )
        # Resident B – outside risk zone (Guwahati)
        resident_b = User(
            id=uuid.uuid4(), full_name="Pranab Das", phone_number="+919876543211",
            email="pranab.das@example.com", password_hash=hash_password("resident123"),
            role=UserRole.RESIDENT, latitude=26.1445, longitude=91.7362,
            location=from_shape(Point(91.7362, 26.1445), srid=4326),
            locality="Paltan Bazaar", district="Kamrup Metropolitan", state="Assam",
        )
        # Resident C – inside zone (near Shillong)
        resident_c = User(
            id=uuid.uuid4(), full_name="Kong Rida Lyngdoh", phone_number="+919876543212",
            password_hash=hash_password("resident123"), role=UserRole.RESIDENT,
            latitude=25.5700, longitude=91.8800,
            location=from_shape(Point(91.8800, 25.5700), srid=4326),
            locality="Police Bazaar", district="East Khasi Hills", state="Meghalaya",
        )
        # Authority
        authority = User(
            id=uuid.uuid4(), full_name="Dr. Ibanri Phanbuh", phone_number="+919876543220",
            email="authority@terraguard.demo", password_hash=hash_password("authority123"),
            role=UserRole.AUTHORITY, latitude=25.5788, longitude=91.8933,
            location=from_shape(Point(91.8933, 25.5788), srid=4326),
            district="East Khasi Hills", state="Meghalaya",
        )
        # Response Team
        response_team = User(
            id=uuid.uuid4(), full_name="Cpt. Mebanshailang Dkhar", phone_number="+919876543230",
            password_hash=hash_password("response123"), role=UserRole.RESPONSE_TEAM,
            latitude=25.5788, longitude=91.8933,
            location=from_shape(Point(91.8933, 25.5788), srid=4326),
            district="East Khasi Hills", state="Meghalaya",
        )
        # Admin
        admin = User(
            id=uuid.uuid4(), full_name="Admin TerraGuard", phone_number="+919876543200",
            email="admin@terraguard.demo", password_hash=hash_password("admin123"),
            role=UserRole.ADMIN, latitude=25.5788, longitude=91.8933,
            location=from_shape(Point(91.8933, 25.5788), srid=4326),
            district="East Khasi Hills", state="Meghalaya",
        )

        db.add_all([resident_a, resident_b, resident_c, authority, response_team, admin])

        # ── Weather Data ─────────────────────────────────────────────────
        for i in range(5):
            db.add(WeatherData(
                id=uuid.uuid4(), source="DEMO – OpenWeatherMap",
                temperature=22 + i, humidity=85 - i*2, pressure=1008 + i,
                wind_speed=12 + i, description="Heavy rain" if i > 2 else "Overcast",
                latitude=25.57 + i*0.01, longitude=91.88 + i*0.01,
                location=from_shape(Point(91.88 + i*0.01, 25.57 + i*0.01), srid=4326),
                recorded_at=now - timedelta(hours=i*6),
            ))

        # ── Rainfall Data ────────────────────────────────────────────────
        for i in range(5):
            db.add(RainfallData(
                id=uuid.uuid4(), source="DEMO – IMD Rainfall",
                rainfall_1h=15 + i*8, rainfall_6h=50 + i*20,
                rainfall_24h=120 + i*30, rainfall_72h=300 + i*50,
                cumulative_rainfall=500 + i*80,
                latitude=25.57 + i*0.01, longitude=91.88 + i*0.01,
                location=from_shape(Point(91.88 + i*0.01, 25.57 + i*0.01), srid=4326),
                recorded_at=now - timedelta(hours=i*6),
            ))

        # ── Satellite Data ───────────────────────────────────────────────
        db.add(SatelliteData(
            id=uuid.uuid4(), source="DEMO – Sentinel-2",
            ndvi=0.45, soil_moisture=0.72, land_cover=3,
            latitude=25.57, longitude=91.88,
            location=from_shape(Point(91.88, 25.57), srid=4326),
            recorded_at=now - timedelta(hours=12),
        ))

        # ── Terrain Data ─────────────────────────────────────────────────
        db.add(TerrainData(
            id=uuid.uuid4(), source="DEMO – SRTM DEM",
            elevation=1100, slope=32, aspect=180, curvature=-0.02,
            latitude=25.57, longitude=91.88,
            location=from_shape(Point(91.88, 25.57), srid=4326),
        ))

        # ── Historical Landslides ────────────────────────────────────────
        for i, (lat, lng, desc) in enumerate([
            (25.58, 91.89, "Sohra landslide – monsoon season 2023"),
            (25.55, 91.87, "Laitlyngkot road collapse – 2022"),
            (25.60, 91.90, "Mawsynram debris flow – 2021"),
        ]):
            db.add(HistoricalLandslide(
                id=uuid.uuid4(), source="DEMO – USGS/GSI",
                description=desc, severity="HIGH",
                latitude=lat, longitude=lng,
                location=from_shape(Point(lng, lat), srid=4326),
                occurred_at=now - timedelta(days=365*(i+1)),
            ))

        # ── Model Version ────────────────────────────────────────────────
        db.add(ModelVersion(
            id=uuid.uuid4(), name="XGBoost Landslide Risk Model",
            version="xgboost-v1", training_date=now,
            feature_schema={
                "features": [
                    "rainfall_1h", "rainfall_6h", "rainfall_24h", "rainfall_72h",
                    "slope", "elevation", "soil_moisture", "land_cover",
                    "historical_landslide_density",
                ]
            },
            metadata_={"note": "Trained on synthetic NER-representative data"},
            is_active=True,
        ))

        # ── Data Sources ─────────────────────────────────────────────────
        sources = [
            ("OpenWeatherMap", "weather", DataSourceStatus.DEMO),
            ("IMD Rainfall", "rainfall", DataSourceStatus.DEMO),
            ("Sentinel-1 SAR", "satellite", DataSourceStatus.DEMO),
            ("Sentinel-2 Optical", "satellite", DataSourceStatus.DEMO),
            ("SRTM DEM", "terrain", DataSourceStatus.DEMO),
            ("USGS Landslide Catalog", "historical", DataSourceStatus.DEMO),
        ]
        for name, stype, status in sources:
            db.add(DataSource(
                id=uuid.uuid4(), name=name, source_type=stype,
                status=status, last_successful_update=now,
            ))

        # ── Demo Risk Zone (Shillong area) ───────────────────────────────
        from geoalchemy2.shape import from_shape as fs
        polygon = create_circle_polygon(25.5788, 91.8933, 5.0)
        zone = RiskZone(
            id=uuid.uuid4(), name="Shillong East – Demo Zone",
            risk_score=0.72, risk_level=RiskLevel.HIGH,
            model_version="xgboost-v1",
            geometry=fs(polygon, srid=4326),
            center_lat=25.5788, center_lng=91.8933, radius_km=5.0,
            environmental_factors={
                "rainfall_24h": "HIGH", "slope": "HIGH",
                "soil_moisture": "MODERATE", "elevation": "MODERATE",
            },
            is_active=True,
        )
        db.add(zone)

        # ── Demo Community Report ────────────────────────────────────────
        db.add(CommunityReport(
            id=uuid.uuid4(), user_id=resident_a.id,
            category=ReportCategory.GROUND_CRACK,
            description="Visible cracks observed on the hillside near Laitumkhrah road. Approximately 2m long.",
            latitude=25.5790, longitude=91.8940,
            location=from_shape(Point(91.8940, 25.5790), srid=4326),
            status=ReportStatus.PENDING,
        ))

        await db.commit()
        print("✅ Database seeded successfully with NER demo data!")
        print(f"   Users: 6 (3 residents, 1 authority, 1 response team, 1 admin)")
        print(f"   Demo credentials:")
        print(f"     Resident A:     +919876543210 / resident123")
        print(f"     Resident B:     +919876543211 / resident123")
        print(f"     Authority:      +919876543220 / authority123")
        print(f"     Response Team:  +919876543230 / response123")
        print(f"     Admin:          +919876543200 / admin123")


if __name__ == "__main__":
    asyncio.run(seed())
