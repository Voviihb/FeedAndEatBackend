from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ReviewCreate(BaseModel):
    mark: float = Field(..., ge=0.5, le=5.0, description="Оценка от 0.5 до 5")

    @field_validator("mark")
    @classmethod
    def round_to_half(cls, v: float) -> float:
        """Округляем до ближайшего 0.5"""
        return round(v * 2) / 2


class ReviewRead(BaseModel):
    id: UUID
    recipe_id: UUID
    user_id: UUID
    mark: float
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
