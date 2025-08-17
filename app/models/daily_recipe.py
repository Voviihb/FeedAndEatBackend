from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class DailyRecipe(Base):
    __tablename__ = "daily_recipe"

    day_of_year = Column(Integer, primary_key=True)  # 1..366
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow) 