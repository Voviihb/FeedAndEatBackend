from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.device_token import DeviceToken
from app.models.user import User
from app.schemas.device_token import DeviceTokenRegister, DeviceTokenRead

router = APIRouter()


@router.post("/register", response_model=DeviceTokenRead, status_code=status.HTTP_201_CREATED)
async def register_device(
    data: DeviceTokenRegister,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Проверяем, нет ли такого токена
    res = await session.execute(select(DeviceToken).where(DeviceToken.token == data.token))
    existing = res.scalar()
    if existing:
        raise HTTPException(status_code=400, detail="Token already registered")
    dt = DeviceToken(user_id=current_user.id, token=data.token, platform=data.platform)
    session.add(dt)
    await session.commit()
    await session.refresh(dt)
    return dt


@router.delete("/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device(
    token: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(DeviceToken).where(DeviceToken.token == token))
    dt: DeviceToken | None = res.scalar()
    if dt and dt.user_id == current_user.id:
        await session.execute(delete(DeviceToken).where(DeviceToken.id == dt.id))
        await session.commit()
    return None 