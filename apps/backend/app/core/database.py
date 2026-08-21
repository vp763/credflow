# CredFlow Backend - Database Configuration

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import event, text
from fastapi import Request, HTTPException

from app.core.config import settings
from app.models.base import Base


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,
    # Use NullPool for testing
    poolclass=NullPool if settings.APP_ENV == "test" else None,
)


# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def init_db() -> None:
    """Initialize database - create tables if not exist."""
    async with engine.begin() as conn:
        # Create extensions
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all tables - use with caution!"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic commit/rollback."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with get_db_session() as session:
        yield session


# Tenant-aware session context
class TenantSessionContext:
    """Context manager for tenant-isolated database operations."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.session: AsyncSession | None = None
        self._original_tenant_id: str | None = None

    async def __aenter__(self) -> AsyncSession:
        self.session = async_session_maker()
        # Set tenant context for RLS
        await self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
            {"tenant_id": self.tenant_id},
        )
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()


# Event listeners for connection lifecycle
@event.listens_for(engine.sync_engine, "connect")
def set_tenant_context(dbapi_connection, connection_record):
    """Set default tenant context on new connections."""
    # This runs in sync context, tenant will be set per-request via middleware
    pass


@event.listens_for(engine.sync_engine, "checkout")
def checkout_connection(dbapi_connection, connection_record, connection_proxy):
    """Reset tenant context on connection checkout from pool."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT set_config('app.tenant_id', '', false)")
    finally:
        cursor.close()


async def get_tenant_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Tenant-aware DB session - sets app.tenant_id for RLS."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context missing")
    async with TenantSessionContext(str(tenant_id)) as session:
        yield session