from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.models.collection import Collection
from app.schemas.user import Token, UserCreate, UserLogin

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
    # Приводим email к нижнему регистру
    email_lower = user_in.email.lower()

    # Проверяем, что email ещё не занят
    res = await session.execute(select(User).where(User.email == email_lower))
    if res.scalar():
        raise HTTPException(status_code=400, detail="Email already registered")

    res = await session.execute(select(User).where(User.username == user_in.username))
    if res.scalar():
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed = get_password_hash(user_in.password)
    user = User(email=email_lower, username=user_in.username, hashed_password=hashed)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Автоматически создаём коллекцию "Избранное" для нового пользователя
    favourites_collection = Collection(name="Избранное", owner_id=user.id)
    session.add(favourites_collection)
    await session.commit()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, session: AsyncSession = Depends(get_session)):
    # Приводим email к нижнему регистру
    email_lower = user_in.email.lower()
    res = await session.execute(select(User).where(User.email == email_lower))
    user: Optional[User] = res.scalar()
    if user is None or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return Token(access_token=access_token, refresh_token=refresh_token)


# --- OAuth2 token endpoint ---

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    # В поле username передаём email, приводим к нижнему регистру
    email_lower = form_data.username.lower()
    res = await session.execute(select(User).where(User.email == email_lower))
    user: Optional[User] = res.scalar()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return Token(access_token=access_token, refresh_token=refresh_token)


# --- Refresh token endpoint ---

class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
):
    payload = decode_refresh_token(body.refresh_token)
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")

    res = await session.execute(select(User).where(User.id == user_id))
    user: Optional[User] = res.scalar()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")

    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    return Token(access_token=access_token, refresh_token=new_refresh_token)
