from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class CollectionBase(BaseModel):
    name: str


class CollectionCreate(CollectionBase):
    pass


class CollectionRead(CollectionBase):
    id: UUID
    picture_url: Optional[str] = None
    created_at: datetime
    recipe_ids: List[UUID] = []

    model_config = {"from_attributes": True}


# Лёгкая версия без списка рецептов
class CollectionBrief(CollectionBase):
    id: UUID
    picture_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True} 