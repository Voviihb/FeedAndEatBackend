from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
import uuid, shutil, os
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.config import settings
from app.models.user import User
from app.schemas.user import ProfileUpdate, UserRead

router = APIRouter()


@router.get("/{user_id}", response_model=UserRead)
async def get_user_profile(user_id: UUID, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(User).where(User.id == user_id))
    user: Optional[User] = res.scalar()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user_profile(
    user_id: UUID,
    data: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(User).where(User.id == user_id))
    user: Optional[User] = res.scalar()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        await session.execute(
            update(User).where(User.id == user_id).values(**update_data)
        )
        await session.commit()

    await session.refresh(user)
    return user


# ---- Upload avatar ----


@router.post("/{user_id}/avatar", response_model=UserRead)
async def upload_avatar(
    user_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    # проверяем, что пользователь существует
    res = await session.execute(select(User).where(User.id == user_id))
    user: Optional[User] = res.scalar()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # сохраняем файл на диск
    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"{uuid.uuid4()}{ext}"
    avatars_dir = Path(settings.MEDIA_DIR) / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    file_path = avatars_dir / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # формируем URL для доступа
    avatar_url = f"{settings.MEDIA_URL}/avatars/{filename}"

    # обновляем запись пользователя
    await session.execute(
        update(User).where(User.id == user_id).values(avatar_url=avatar_url)
    )
    await session.commit()
    await session.refresh(user)

    return user 