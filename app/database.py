from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "sqlite" in DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_async_engine(
        DATABASE_URL, 
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

AsyncSessionLocal = async_sessionmaker(class_=AsyncSession, autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()