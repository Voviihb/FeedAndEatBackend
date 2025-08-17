from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text, or_

from app.core.database import get_session
from app.core.config import settings
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate, RecipeRead
from app.models.user import User
from app.core.security import get_current_user
from app.models.daily_recipe import DailyRecipe

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


# ---- Search / filter ----
@router.get("/search", response_model=List[RecipeRead])
async def search_recipes(
        q: Optional[str] = Query(None, description="Поисковая строка"),
        tags: Optional[List[str]] = Query(None, description="Список тегов (OR)"),
        calories_min: Optional[float] = Query(None),
        calories_max: Optional[float] = Query(None),
        protein_min: Optional[float] = Query(None),
        protein_max: Optional[float] = Query(None),
        fat_min: Optional[float] = Query(None),
        fat_max: Optional[float] = Query(None),
        carbs_min: Optional[float] = Query(None),
        carbs_max: Optional[float] = Query(None),
        sugar_min: Optional[float] = Query(None),
        sugar_max: Optional[float] = Query(None),
        sort: str = Query("new", enum=["new", "rating", "popularity"]),
        limit: int = Query(20, le=100),
        offset: int = Query(0, ge=0),
        session: AsyncSession = Depends(get_session),
):
    stmt = select(Recipe)

    if q:
        stmt = stmt.where(Recipe.name.ilike(f"%{q}%"))

    if tags:
        tag_filters = [Recipe.tags.contains([tag]) for tag in tags]
        stmt = stmt.where(or_(*tag_filters))

    def between(json_key: str, min_val: Optional[float], max_val: Optional[float]):
        nonlocal stmt
        if min_val is not None:
            stmt = stmt.where(Recipe.nutrients[json_key].as_float() >= min_val)  # type: ignore
        if max_val is not None:
            stmt = stmt.where(Recipe.nutrients[json_key].as_float() <= max_val)  # type: ignore

    between("Calories", calories_min, calories_max)
    between("Protein", protein_min, protein_max)
    between("Fat", fat_min, fat_max)
    between("Carbohydrates", carbs_min, carbs_max)
    between("Sugar", sugar_min, sugar_max)

    if sort == "new":
        stmt = stmt.order_by(desc(Recipe.created_at))
    elif sort == "rating":
        stmt = stmt.order_by(desc(Recipe.rating))
    elif sort == "popularity":
        stmt = stmt.order_by(desc(Recipe.cooked))

    stmt = stmt.offset(offset).limit(limit)

    res = await session.execute(stmt)
    return res.scalars().all()


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


@router.get("/daily", response_model=RecipeRead)
async def get_daily_recipe(session: AsyncSession = Depends(get_session)):
    from datetime import datetime
    day = datetime.utcnow().timetuple().tm_yday
    res = await session.execute(select(DailyRecipe).where(DailyRecipe.day_of_year == day))
    dr = res.scalar()
    if dr is None:
        raise HTTPException(status_code=404, detail="Daily recipe not set")
    res = await session.execute(select(Recipe).where(Recipe.id == dr.recipe_id))
    recipe = res.scalar()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return recipe


@router.get("/{recipe_id}", response_model=RecipeRead)
async def get_recipe(recipe_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe: Optional[Recipe] = res.scalar()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe
