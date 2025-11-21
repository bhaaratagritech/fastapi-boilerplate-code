from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import AppException
from ..dependencies.rate_limit import rate_limiter
from ..models.user import User
from ..schemas.user import UserCreate, UserRead
from ..services.database.mysql import get_session

router = APIRouter(dependencies=[Depends(rate_limiter)])


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_session)) -> UserRead:
    user = User(email=payload.email, full_name=payload.full_name)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)) -> UserRead:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise AppException("User not found", status_code=404)
    return UserRead.model_validate(user)


@router.get("/", response_model=list[UserRead])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[UserRead]:
    result = await session.execute(select(User))
    users = result.scalars().all()
    return [UserRead.model_validate(user) for user in users]


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise AppException("User not found", status_code=404)
    await session.delete(user)


