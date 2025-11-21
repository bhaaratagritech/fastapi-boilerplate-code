from __future__ import annotations

from typing import Optional

import aio_pika

from ...core.config import Settings
from ...core.logging_config import get_logger

logger = get_logger(__name__)

connection: Optional[aio_pika.RobustConnection] = None


async def init_connection(settings: Settings) -> None:
    """Initialize RabbitMQ connection. Gracefully handles connection errors."""
    global connection
    if connection:
        return

    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        logger.info("Connected to RabbitMQ", extra={"url": settings.rabbitmq_url})
    except Exception as exc:
        logger.error(
            "Failed to connect to RabbitMQ - application will continue without messaging",
            extra={"url": settings.rabbitmq_url, "error": str(exc), "error_type": type(exc).__name__}
        )
        connection = None


async def close_connection() -> None:
    """Close RabbitMQ connection gracefully."""
    global connection
    if connection:
        try:
            await connection.close()
        except Exception as exc:
            logger.warning("Error closing RabbitMQ connection", extra={"error": str(exc)})
        finally:
            connection = None


def get_connection() -> aio_pika.RobustConnection:
    """Get the RabbitMQ connection instance."""
    if not connection:
        raise RuntimeError("RabbitMQ connection not initialised - RabbitMQ connection unavailable")
    return connection


