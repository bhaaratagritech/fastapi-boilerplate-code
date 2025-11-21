from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(include_in_schema=False)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


