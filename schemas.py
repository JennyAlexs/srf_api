from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional


# ┌─────────────────────────────────────────────────────────────┐
# │ LOCATION SCHEMAS                                            │
class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    capacity: int = Field(default=10, ge=1, le=1000)


class LocationCreate(LocationBase):
    pass


class LocationResponse(LocationBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True


# ┌─────────────────────────────────────────────────────────────┐
# │ USER SCHEMAS                                                │
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


# ┌─────────────────────────────────────────────────────────────┐
# │ FACILITY SCHEMAS                                            │
class FacilityBase(BaseModel):
    location_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    max_participants: int = Field(default=10, ge=1, le=100)
    price: float = Field(default=0.0, ge=0.0)


class FacilityCreate(FacilityBase):
    pass


class FacilityResponse(FacilityBase):
    id: int
    current_participants: int = 0
    is_active: bool = True
    location: Optional[LocationResponse] = None

    class Config:
        from_attributes = True


# ┌─────────────────────────────────────────────────────────────┐
# │ BOOKING SCHEMAS                                             │
class BookingBase(BaseModel):
    user_id: int
    facility_id: int


class BookingCreate(BookingBase):
    pass


class BookingResponse(BookingBase):
    id: int
    created_at: datetime
    status: str = "confirmed"
    cancelled_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    facility: Optional[FacilityResponse] = None

    class Config:
        from_attributes = True


# ┌─────────────────────────────────────────────────────────────┐
# │ SCIENCE NEWS SCHEMAS                                        │
class NewsBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    url: str = Field(..., min_length=1, max_length=500)
    source: str = Field(default="unknown")
    summary: Optional[str] = None


class NewsCreate(NewsBase):
    pass


class NewsResponse(NewsBase):
    id: int
    published_at: datetime
    scraped_at: datetime

    class Config:
        from_attributes = True
