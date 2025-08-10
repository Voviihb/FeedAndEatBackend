from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    name = Column(String(255), nullable=False)
    image_url = Column(String, nullable=True)

    instructions = Column(JSONB, nullable=False, default=list)  # List[Instruction]
    servings = Column(JSONB, nullable=True)  # {amount, weight}
    ingredients = Column(JSONB, nullable=False, default=list)  # List[Ingredient]
    tags = Column(JSONB, nullable=True)  # List[str]
    nutrients = Column(JSONB, nullable=True)  # {Calories, Sugar, Protein, Fat, Carbohydrates}

    rating = Column(Float, default=0.0)
    cooked = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="recipes")
    collections = relationship("Collection", secondary="collection_recipes", back_populates="recipes")

    def __repr__(self) -> str:
        return f"<Recipe {self.id} {self.name}>" 