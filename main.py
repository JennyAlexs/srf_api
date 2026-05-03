from datetime import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter

from database import engine, get_db, Base
from models import Location, User, Facility, Booking, ScienceNews
from schemas import (
    LocationCreate, LocationResponse,
    UserCreate, UserResponse,
    FacilityCreate, FacilityResponse,
    BookingCreate, BookingResponse,
    NewsCreate, NewsResponse
)
from dependencies import require_role
from auth.routes import router as auth_router

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(
    title="Srf Booking API",
    description="API для бронирования научного оборудования",
    version="2.0.0"
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://mysrf.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net"
    )
    response.headers["Content-Security-Policy"] = csp
    return response

app.include_router(auth_router)
check_client_role = require_role("client")


@app.on_event("startup")
async def on_startup():
    """Создаёт таблицы БД при запуске."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База данных инициализирована!")


# ═══════════════════════════════════════════════════════════════
# LOCATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/locations/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(location: LocationCreate, db: AsyncSession = Depends(get_db)):
    db_location = Location(**location.model_dump())
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    return db_location

@app.get("/locations/", response_model=List[LocationResponse])
async def get_locations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Location))
    return result.scalars().all()


# ═══════════════════════════════════════════════════════════════
# USER ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username уже занят")
    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=pwd_context.hash(user.password),
        role="client",
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


# ═══════════════════════════════════════════════════════════════
# FACILITY ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/facilities/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
async def create_facility(facility: FacilityCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Location).where(Location.id == facility.location_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Локация не найдена")
    if facility.end_time <= facility.start_time:
        raise HTTPException(status_code=400, detail="Время окончания должно быть позже начала")
    db_facility = Facility(**facility.model_dump())
    db.add(db_facility)
    await db.commit()
    await db.refresh(db_facility)
    result = await db.execute(
        select(Facility)
        .options(selectinload(Facility.location))
        .where(Facility.id == db_facility.id)
    )
    db_facility = result.scalar_one()
    return db_facility

@app.get("/facilities/", response_model=List[FacilityResponse])
async def get_facilities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Facility).options(selectinload(Facility.location)))
    return result.scalars().all()

@app.get("/facilities/{facility_id}", response_model=FacilityResponse)
async def get_facility(facility_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Facility).options(selectinload(Facility.location)).where(Facility.id == facility_id)
    )
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return facility


# ═══════════════════════════════════════════════════════════════
# BOOKING ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/bookings/", response_model=BookingResponse, status_code=201)
@limiter.limit("10/minute")
async def create_booking(
    request: Request,
    booking: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(check_client_role)
):
    result = await db.execute(select(User).where(User.id == booking.user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь не найден")
    result = await db.execute(select(Facility).where(Facility.id == booking.facility_id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=400, detail="Сессия не найдена")
    if facility.current_participants >= facility.max_participants:
        raise HTTPException(status_code=400, detail="Нет свободных мест")
    result = await db.execute(
        select(Booking).where(
            (Booking.user_id == booking.user_id) & (Booking.facility_id == booking.facility_id)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже записаны на эту сессию")
    db_booking = Booking(**booking.model_dump())
    db.add(db_booking)
    facility.current_participants += 1
    await db.commit()
    await db.refresh(db_booking)
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.user),
            selectinload(Booking.facility).selectinload(Facility.location)
        )
        .where(Booking.id == db_booking.id)
    )
    db_booking = result.scalar_one()
    return db_booking

@app.get("/bookings/", response_model=List[BookingResponse])
async def get_bookings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Booking).options(
            selectinload(Booking.user),
            selectinload(Booking.facility).selectinload(Facility.location)
        )
    )
    return result.scalars().all()

@app.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    facility_result = await db.execute(select(Facility).where(Facility.id == booking.facility_id))
    facility = facility_result.scalar_one_or_none()
    if facility:
        facility.current_participants = max(0, facility.current_participants - 1)
    await db.delete(booking)
    await db.commit()
    return None


# ═══════════════════════════════════════════════════════════════
# SCIENCE NEWS ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/news/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(news: NewsCreate, db: AsyncSession = Depends(get_db)):
    db_news = ScienceNews(**news.model_dump())
    db.add(db_news)
    await db.commit()
    await db.refresh(db_news)
    return db_news

@app.get("/news/", response_model=List[NewsResponse])
async def get_news(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScienceNews))
    return result.scalars().all()


# ═══════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.get("/analytics/facility-usage", response_model=dict)
async def facility_usage_analytics(db: AsyncSession = Depends(get_db)):
    """Аналитика загрузки оборудования с рекомендацией."""
    result = await db.execute(
        select(Facility).options(selectinload(Facility.location))
    )
    facilities = result.scalars().all()
    if not facilities:
        return {"message": "Нет данных об оборудовании"}

    facility_stats = []
    for facility in facilities:
        usage_percent = round(
            (facility.current_participants / facility.max_participants) * 100, 1
        ) if facility.max_participants > 0 else 0
        facility_stats.append({
            "facility_id": facility.id,
            "facility_name": facility.name,
            "location": facility.location.name if facility.location else "N/A",
            "max_participants": facility.max_participants,
            "current_participants": facility.current_participants,
            "usage_percent": usage_percent,
            "available_spots": facility.max_participants - facility.current_participants,
            "start_time": facility.start_time.isoformat() if facility.start_time else None,
            "end_time": facility.end_time.isoformat() if facility.end_time else None,
            "is_active": facility.is_active
        })

    facility_stats.sort(key=lambda x: x["usage_percent"])

    location_stats = {}
    for stat in facility_stats:
        loc = stat["location"]
        if loc not in location_stats:
            location_stats[loc] = {"total_facilities": 0, "total_capacity": 0, "total_booked": 0}
        location_stats[loc]["total_facilities"] += 1
        location_stats[loc]["total_capacity"] += stat["max_participants"]
        location_stats[loc]["total_booked"] += stat["current_participants"]

    for loc, data in location_stats.items():
        cap = data["total_capacity"]
        booked = data["total_booked"]
        data["usage_percent"] = round((booked / cap) * 100, 1) if cap > 0 else 0

    total_capacity = sum(f.max_participants for f in facilities)
    total_booked = sum(f.current_participants for f in facilities)
    overall_usage = round((total_booked / total_capacity) * 100, 1) if total_capacity > 0 else 0

    recommendation = facility_stats[0] if facility_stats else None

    return {
        "overall_stats": {
            "total_facilities": len(facilities),
            "total_capacity": total_capacity,
            "total_booked": total_booked,
            "overall_usage_percent": overall_usage
        },
        "location_stats": location_stats,
        "facility_details": facility_stats,
        "recommendation": {
            "message": "Рекомендуемое оборудование (наименьшая загрузка)",
            "facility": recommendation
        }
    }


# ═══════════════════════════════════════════════════════════════
# ROOT ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return {
        "message": "Srf Booking API v2.0",
        "status": "online",
        "endpoints": [
            "/locations/",
            "/users/",
            "/facilities/",
            "/bookings/",
            "/news/"
        ]
    }
