from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ...core.config import Settings
from ...core.exceptions import AppException
from ...core.logging_config import get_logger
from ...models import base

logger = get_logger(__name__)

engine: Optional[AsyncEngine] = None
session_factory: Optional[async_sessionmaker[AsyncSession]] = None


async def init_engine(settings: Settings) -> None:
    """Initialise the async engine and session factory. Gracefully handles connection errors."""
    global engine, session_factory
    if engine:
        return

    try:
        engine = create_async_engine(settings.mysql_dsn, echo=False, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(base.Base.metadata.create_all)

        logger.info("Connected to MySQL", extra={"dsn": settings.mysql_dsn})
    except Exception as exc:
        logger.error(
            "Failed to connect to MySQL - application will continue without database",
            extra={"dsn": settings.mysql_dsn, "error": str(exc), "error_type": type(exc).__name__}
        )
        engine = None
        session_factory = None


async def shutdown_engine() -> None:
    """Shutdown the database engine gracefully."""
    global engine
    if engine:
        try:
            await engine.dispose()
        except Exception as exc:
            logger.warning("Error disposing MySQL engine", extra={"error": str(exc)})
        finally:
            engine = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if not session_factory:
        raise AppException(
            "Database connection unavailable. Ensure MySQL is running and `MYSQL_DSN` is correct.",
            status_code=503,
        )

    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def check_status(settings: Settings) -> bool:
    """Check whether MySQL is reachable."""
    temp_engine: Optional[AsyncEngine] = None
    try:
        temp_engine = create_async_engine(settings.mysql_dsn, echo=False, pool_pre_ping=True)
        async with temp_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Dependency check: MySQL is running", extra={"dsn": settings.mysql_dsn})
        return True
    except Exception as exc:
        logger.error(
            "Dependency check: MySQL is NOT running",
            extra={"dsn": settings.mysql_dsn, "error": str(exc), "error_type": type(exc).__name__},
        )
        return False
    finally:
        if temp_engine:
            await temp_engine.dispose()


