from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies.rate_limit import rate_limiter
from ..services.cache import redis_cache

router = APIRouter(dependencies=[Depends(rate_limiter)])


@router.post("/{key}")
async def set_cache_entry(key: str, payload: dict, ttl: int = 300) -> dict:
    await redis_cache.cache_response(key, payload, ttl=ttl)
    return {"status": "cached", "key": key, "ttl": ttl}


@router.get("/{key}")
async def get_cache_entry(key: str) -> dict:
    cached = await redis_cache.get_cached_response(key)
    if cached is None:
        raise HTTPException(status_code=404, detail="Cache miss")
    return {"key": key, "value": cached}


