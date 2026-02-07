"""Database engine, session, and base for SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import settings

# Sync engine for Base.metadata.create_all (app lifespan and tests). Alembic uses its own engine in env.py.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine and session for request handlers
_async_url = (
    settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if settings.DATABASE_URL.startswith("sqlite")
    else settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    if settings.DATABASE_URL.startswith("postgresql")
    else settings.DATABASE_URL
)
async_engine = create_async_engine(_async_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, autocommit=False, autoflush=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


async def get_db():
    """Async dependency that yields a DB session for FastAPI."""
    async with AsyncSessionLocal() as session:
        yield session
