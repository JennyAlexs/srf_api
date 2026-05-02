import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from passlib.context import CryptContext
from datetime import datetime, timedelta

from main import app
from models import User, Location, Facility
from database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test_srf.db"
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Создаёт таблицы и тестовые данные один раз на все тесты"""
    import asyncio
    import sqlalchemy
    
    sync_url = "sqlite:///./test_srf.db"
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=sync_engine)
    
    SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    
    with SyncSessionLocal() as session:
        existing = session.query(User).filter(User.username == "test_client").first()
        if not existing:
            test_user = User(
                username="test_client",
                email="test_client@example.com",
                password_hash=pwd_context.hash("secure123"),
                role="client"
            )
            session.add(test_user)
        
        existing_loc = session.query(Location).filter(Location.name == "Test Location").first()
        if not existing_loc:
            test_location = Location(
                name="Test Location",
                description="Test location for tests",
                capacity=10,
                is_active=True
            )
            session.add(test_location)
            session.flush()
            
            test_facility = Facility(
                location_id=test_location.id,
                name="Test Facility",
                description="Test facility for tests",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=2),
                max_participants=10,
                current_participants=0,
                price=100.0,
                is_active=True
            )
            session.add(test_facility)
        
        session.commit()
    yield

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()