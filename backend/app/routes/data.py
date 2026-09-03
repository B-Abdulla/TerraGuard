"""Data routes: weather, rainfall, data sources."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import WeatherData, RainfallData, DataSource

router = APIRouter(prefix="/api/v1", tags=["Data"])


@router.get("/weather")
async def get_weather(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeatherData).order_by(WeatherData.recorded_at.desc()).limit(50)
    )
    data = result.scalars().all()
    return {
        "data": [
            {
                "id": str(w.id), "source": w.source, "temperature": w.temperature,
                "humidity": w.humidity, "pressure": w.pressure, "wind_speed": w.wind_speed,
                "description": w.description, "latitude": w.latitude, "longitude": w.longitude,
                "recorded_at": w.recorded_at.isoformat() if w.recorded_at else None,
            }
            for w in data
        ],
        "count": len(data),
    }


@router.get("/rainfall")
async def get_rainfall(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RainfallData).order_by(RainfallData.recorded_at.desc()).limit(50)
    )
    data = result.scalars().all()
    return {
        "data": [
            {
                "id": str(r.id), "source": r.source,
                "rainfall_1h": r.rainfall_1h, "rainfall_6h": r.rainfall_6h,
                "rainfall_24h": r.rainfall_24h, "rainfall_72h": r.rainfall_72h,
                "cumulative_rainfall": r.cumulative_rainfall,
                "latitude": r.latitude, "longitude": r.longitude,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in data
        ],
        "count": len(data),
    }
