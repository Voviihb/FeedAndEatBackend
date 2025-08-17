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
from app.core.security import get_current_user

router = APIRouter()


# ---- Helpers ----
def _public_user(user: User, owner: bool) -> User:
    """Возвращает объект пользователя с учётом приватности."""
    if owner or not user.is_profile_private:
        return user
    # скрываем чувствительные поля
    user.avatar_url = None
    user.about_me = None
    user.theme_settings = ""  # или оставить текущий
    return user


# ---- Current user ----
@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ---- Other user ----
@router.get("/{user_id}", response_model=UserRead)
async def get_user_profile(
    user_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(User).where(User.id == user_id))
    user: Optional[User] = res.scalar()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    owner = current_user is not None and current_user.id == user.id
    user = _public_user(user, owner)
    return user


@router.put("/me", response_model=UserRead)
async def update_my_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        await session.execute(update(User).where(User.id == current_user.id).values(**update_data))
        await session.commit()
    await session.refresh(current_user)
    return current_user


# ---- Upload avatar ----
@router.post("/me/avatar", response_model=UserRead)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = current_user

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
    await session.execute(update(User).where(User.id == user.id).values(avatar_url=avatar_url))
    await session.commit()
    await session.refresh(user)

    return user 