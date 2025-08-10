from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class TagRead(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True} 