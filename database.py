from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. URL подключения (обязательно на верхнем уровне!)
DATABASE_URL = "sqlite+aiosqlite:///./srf.db"

# 2. Движок — должен быть переменной модуля, НЕ внутри функции!
engine = create_async_engine(DATABASE_URL, echo=True)

# 3. Фабрика сессий
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 4. Базовый класс для моделей
Base = declarative_base()

# 5. Зависимость для FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
