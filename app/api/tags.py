from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.models.tag import Tag
from app.schemas.tag import TagRead

router = APIRouter()


@router.get("/", response_model=List[TagRead])
async def list_tags(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Tag).order_by(Tag.name))
    return res.scalars().all() 