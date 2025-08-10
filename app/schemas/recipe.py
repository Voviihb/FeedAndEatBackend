from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class Instruction(BaseModel):
    paragraph: str
    timers: Optional[List[Dict[str, Any]]] = None


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
    ingredients: List[Ingredient]
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