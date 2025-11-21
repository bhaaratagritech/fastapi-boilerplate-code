from fastapi import APIRouter

from . import cache, health, messages, search, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])


