from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    is_active: bool
    avatar_url: Optional[str] = None
    about_me: Optional[str] = None
    is_profile_private: bool
    theme_settings: str

    model_config = {
        "from_attributes": True,
    }


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer" 


class ProfileUpdate(BaseModel):
    avatar_url: Optional[str] = None
    about_me: Optional[str] = None
    is_profile_private: Optional[bool] = None
    theme_settings: Optional[str] = None 