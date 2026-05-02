"""Модели базы данных SRF Booking API."""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    ForeignKey, Text, Float, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Location(Base):
    """Локации — места проведения сессий."""
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    capacity = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    facilities = relationship("Facility", back_populates="location")

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}')>"


class User(Base):
    """Пользователи системы."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="client")
    created_at = Column(DateTime, default=func.now)
    is_active = Column(Boolean, default=True)
    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Facility(Base):
    """Оборудование/сессии для бронирования."""
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    max_participants = Column(Integer, default=10)
    current_participants = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    location = relationship("Location", back_populates="facilities")
    bookings = relationship("Booking", back_populates="facility")

    def __repr__(self):
        return f"<Facility(id={self.id}, name='{self.name}')>"


class Booking(Base):
    """Бронирования пользователей."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now)
    status = Column(String(50), default="confirmed")
    cancelled_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="bookings")
    facility = relationship("Facility", back_populates="bookings")
    __table_args__ = (
        UniqueConstraint('user_id', 'facility_id', name='unique_user_facility'),
    )

    def __repr__(self):
        return f"<Booking(id={self.id}, user={self.user_id}, facility={self.facility_id})>"


class ScienceNews(Base):
    """Новости науки."""
    __tablename__ = "science_news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    url = Column(String(500), nullable=False, unique=True, index=True)
    source = Column(String(100), default="unknown")
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime, default=func.now)
    scraped_at = Column(DateTime, default=func.now)

    def __repr__(self):
        return f"<ScienceNews(id={self.id}, title='{self.title[:30]}...')>"
