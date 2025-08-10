from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text

from app.core.database import get_session
from app.core.config import settings
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate, RecipeRead
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter()


@router.post("/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    recipe_data = data.model_dump()
    recipe_data["user_id"] = current_user.id
    recipe = Recipe(**recipe_data)
    session.add(recipe)
    await session.commit()
    await session.refresh(recipe)
    return recipe


@router.post("/{recipe_id}/image", response_model=RecipeRead)
async def upload_recipe_image(
    recipe_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Проверяем, что рецепт существует и принадлежит текущему пользователю
    res = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe: Optional[Recipe] = res.scalar()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # MIME и размер (<=5MB)
    if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    # сохраняем
    ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[file.content_type]
    filename = f"{uuid.uuid4()}{ext}"
    recipes_dir = Path(settings.MEDIA_DIR) / "recipes"
    recipes_dir.mkdir(parents=True, exist_ok=True)
    file_path = recipes_dir / filename
    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    recipe.image_url = f"{settings.MEDIA_URL}/recipes/{filename}"
    await session.commit()
    await session.refresh(recipe)
    return recipe


@router.get("/{recipe_id}", response_model=RecipeRead)
async def get_recipe(recipe_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe: Optional[Recipe] = res.scalar()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


# ---- Подборки ----

@router.get("/top", response_model=List[RecipeRead])
async def top_recipes(limit: int = Query(10, le=100), session: AsyncSession = Depends(get_session)):
    res = await session.execute(
        select(Recipe).order_by(desc(Recipe.rating)).limit(limit)
    )
    return res.scalars().all()


@router.get("/latest", response_model=List[RecipeRead])
async def latest_recipes(limit: int = Query(10, le=100), session: AsyncSession = Depends(get_session)):
    res = await session.execute(
        select(Recipe).order_by(desc(Recipe.created_at)).limit(limit)
    )
    return res.scalars().all()


@router.get("/low_calorie", response_model=List[RecipeRead])
async def low_calorie_recipes(
    max_calories: float = Query(100.0),
    limit: int = Query(10, le=100),
    session: AsyncSession = Depends(get_session),
):
    # nutrients ->> 'Calories' as numeric <= max_calories
    stmt = (
        select(Recipe)
        .where(
            (Recipe.nutrients["Calories"].as_float() <= max_calories)  # type: ignore
        )
        .order_by(desc(Recipe.cooked))
        .limit(limit)
    )
    res = await session.execute(stmt)
    return res.scalars().all() 