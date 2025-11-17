"""
Database session management using SQLAlchemy 2.0 async patterns.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings


class Base(DeclarativeBase):
    """
    Base class for all database models.
    Uses SQLAlchemy 2.0 declarative base.
    """
    pass


# Create async engine
def create_engine() -> AsyncEngine:
    """
    Create and configure the async database engine.

    Returns:
        AsyncEngine: Configured async SQLAlchemy engine
    """
    # NullPool doesn't support pool_size, max_overflow parameters
    if settings.ENVIRONMENT == "production":
        engine = create_async_engine(
            str(settings.DATABASE_URL),
            echo=settings.DEBUG,
            future=True,
            pool_pre_ping=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
            poolclass=QueuePool,
        )
    else:
        engine = create_async_engine(
            str(settings.DATABASE_URL),
            echo=settings.DEBUG,
            future=True,
            poolclass=NullPool,
        )
    return engine


# Create engine instance
engine = create_engine()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session for dependency injection

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    Note:
        In production, use Alembic migrations instead.
        This is useful for development and testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.

    Should be called on application shutdown.
    """
    await engine.dispose()
