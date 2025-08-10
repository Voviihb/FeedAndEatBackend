from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

collection_recipes = Table(
    "collection_recipes",
    Base.metadata,
    Column("collection_id", UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    Column("recipe_id", UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
)


class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(100), nullable=False)
    picture_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="collections")
    recipes = relationship(
        "Recipe",
        secondary=collection_recipes,
        back_populates="collections",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Collection {self.id} {self.name}>" 