"""FastAPI application entry point for TerraGuard."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import engine, Base
from app.routes import auth, risk, alerts, community, data, system

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="TerraGuard API",
    description="AI-Based Early Warning & Landslide Risk Monitoring System for Northeast India",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(risk.router)
app.include_router(alerts.router)
app.include_router(community.router)
app.include_router(data.router)
app.include_router(system.router)


@app.get("/")
async def root():
    return {
        "name": "TerraGuard API",
        "version": "1.0.0",
        "description": "AI-Based Landslide Risk Monitoring & Early Warning System",
        "status": "running",
        "demo_mode": settings.DEMO_MODE,
    }
