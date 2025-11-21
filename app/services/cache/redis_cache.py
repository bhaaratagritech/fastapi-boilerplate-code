from __future__ import annotations

import json
from typing import Any, Optional

from redis.asyncio import Redis, from_url

from ...core.config import Settings
from ...core.logging_config import get_logger

logger = get_logger(__name__)

redis_client: Optional[Redis] = None


async def init_cache(settings: Settings) -> None:
    """Initialize Redis cache. Gracefully handles connection errors."""
    global redis_client
    if redis_client:
        return

    try:
        redis_client = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        # Test connection by pinging
        await redis_client.ping()
        logger.info("Connected to Redis", extra={"url": settings.redis_url})
    except Exception as exc:
        logger.error(
            "Failed to connect to Redis - application will continue without caching/rate limiting",
            extra={"url": settings.redis_url, "error": str(exc), "error_type": type(exc).__name__}
        )
        redis_client = None


async def close_cache() -> None:
    """Close Redis cache connection gracefully."""
    global redis_client
    if redis_client:
        try:
            await redis_client.aclose()
        except Exception as exc:
            logger.warning("Error closing Redis client", extra={"error": str(exc)})
        finally:
            redis_client = None


def get_client() -> Redis:
    if not redis_client:
        raise RuntimeError("Redis client not initialised - Redis connection unavailable")
    return redis_client


async def cache_response(key: str, value: Any, ttl: int = 300) -> None:
    client = get_client()
    encoded = json.dumps(value)
    await client.set(key, encoded, ex=ttl)


async def get_cached_response(key: str) -> Optional[Any]:
    client = get_client()
    raw = await client.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


