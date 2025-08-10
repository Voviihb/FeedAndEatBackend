from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_session
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
    # Проверяем, что email ещё не занят
    res = await session.execute(select(User).where(User.email == user_in.email))
    if res.scalar():
        raise HTTPException(status_code=400, detail="Email already registered")

    res = await session.execute(select(User).where(User.username == user_in.username))
    if res.scalar():
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed = get_password_hash(user_in.password)
    user = User(email=user_in.email, username=user_in.username, hashed_password=hashed)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(User).where(User.email == user_in.email))
    user: Optional[User] = res.scalar()
    if user is None or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)


# --- OAuth2 token endpoint ---


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    # В поле username передаём email
    res = await session.execute(select(User).where(User.email == form_data.username))
    user: Optional[User] = res.scalar()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token) 