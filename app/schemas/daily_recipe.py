from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class DailyRecipeRead(BaseModel):
    day_of_year: int
    recipe_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True} 