"""Auth routes: register, login, current user."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserRegister, UserLogin, Token, UserResponse
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check duplicate
    existing = await db.execute(select(User).where(User.phone_number == data.phone_number))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    location = None
    if data.latitude is not None and data.longitude is not None:
        location = from_shape(Point(data.longitude, data.latitude), srid=4326)

    user = User(
        id=uuid.uuid4(),
        full_name=data.full_name,
        phone_number=data.phone_number,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole(data.role.value),
        latitude=data.latitude,
        longitude=data.longitude,
        location=location,
        locality=data.locality,
        district=data.district,
        state=data.state,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()

    await log_event(db, "USER_REGISTERED", f"User {data.full_name} registered as {data.role.value}",
                    metadata={"user_id": str(user.id), "role": data.role.value})

    return UserResponse(
        id=str(user.id), full_name=user.full_name, phone_number=user.phone_number,
        email=user.email, role=user.role.value, latitude=user.latitude, longitude=user.longitude,
        locality=user.locality, district=user.district, state=user.state,
        is_active=user.is_active, created_at=user.created_at,
    )


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})

    await log_event(db, "USER_LOGIN", f"User {user.full_name} logged in",
                    metadata={"user_id": str(user.id)})

    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id), full_name=current_user.full_name,
        phone_number=current_user.phone_number, email=current_user.email,
        role=current_user.role.value, latitude=current_user.latitude,
        longitude=current_user.longitude, locality=current_user.locality,
        district=current_user.district, state=current_user.state,
        is_active=current_user.is_active, created_at=current_user.created_at,
    )
