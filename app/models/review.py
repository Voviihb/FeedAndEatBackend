from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mark = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Один пользователь — один отзыв на рецепт
    __table_args__ = (
        UniqueConstraint("recipe_id", "user_id", name="uq_review_recipe_user"),
    )

    recipe = relationship("Recipe", back_populates="reviews")
    author = relationship("User", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review {self.id} recipe={self.recipe_id} user={self.user_id} mark={self.mark}>"
