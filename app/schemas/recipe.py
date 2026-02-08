from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from pydantic import BaseModel, Field


class Timer(BaseModel):
    """Строгая схема для таймеров"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str  # "constant" или "range"
    number: Optional[int] = None  # для type="constant"
    lower_limit: Optional[int] = Field(None, alias="lowerLimit")  # для type="range"
    upper_limit: Optional[int] = Field(None, alias="upperLimit")  # для type="range"

    model_config = {
        "populate_by_name": True,  # позволяет использовать как "lower_limit", так и "lowerLimit"
    }


class Instruction(BaseModel):
    paragraph: str
    timers: Optional[List[Timer]] = None


class Ingredient(BaseModel):
    name: str
    amount: float
    unit: str


class Nutrients(BaseModel):
    Calories: Optional[float] = None
    Sugar: Optional[float] = None
    Protein: Optional[float] = None
    Fat: Optional[float] = None
    Carbohydrates: Optional[float] = None


class Servings(BaseModel):
    amount: Optional[int] = None
    weight: Optional[int] = None


class RecipeBase(BaseModel):
    name: str
    image_url: Optional[str] = None
    instructions: List[Instruction]
    servings: Optional[Servings] = None
    ingredients: Optional[List[Ingredient]] = None
    tags: Optional[List[str]] = None
    nutrients: Optional[Nutrients] = None


class RecipeCreate(RecipeBase):
    pass


class RecipeRead(RecipeBase):
    id: UUID
    user_id: UUID
    rating: float
    cooked: int
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


# ---- Search params ----


class SearchParams(BaseModel):
    q: Optional[str] = None
    calories_min: Optional[float] = None
    calories_max: Optional[float] = None
    protein_min: Optional[float] = None
    protein_max: Optional[float] = None
    fat_min: Optional[float] = None
    fat_max: Optional[float] = None
    carbs_min: Optional[float] = None
    carbs_max: Optional[float] = None
    sugar_min: Optional[float] = None
    sugar_max: Optional[float] = None
    tags: Optional[List[str]] = None  # OR semantics
    sort: Optional[str] = "new"  # new, rating, popularity
    limit: int = 20
    offset: int = 0 