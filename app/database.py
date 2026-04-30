from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "sqlite" in DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Supabase's pooled connection (pgbouncer in transaction mode) doesn't
    # support prepared statements — disable asyncpg's statement cache so it
    # works with both the pooler and a direct connection.
    engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
    )

AsyncSessionLocal = async_sessionmaker(
    class_=AsyncSession, autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
