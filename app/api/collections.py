from __future__ import annotations

import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_session
from app.core.config import settings
from app.core.security import get_current_user
from app.models.collection import Collection, collection_recipes
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.collection import CollectionCreate, CollectionRead
from app.schemas.recipe import RecipeRead
from app.schemas.collection import CollectionBrief

router = APIRouter()


@router.post("/", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    collection = Collection(name=data.name, owner_id=current_user.id)
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return CollectionRead(
        id=collection.id,
        name=collection.name,
        picture_url=collection.picture_url,
        created_at=collection.created_at,
        recipe_ids=[],
    )


# ---- My collections ----
@router.get("/my", response_model=List[CollectionBrief])
async def get_my_collections(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Collection).where(Collection.owner_id == current_user.id))
    collections = res.scalars().all()
    result: List[CollectionBrief] = []
    for col in collections:
        # Получаем картинку последнего рецепта в коллекции
        picture_url = col.picture_url  # Начинаем с собственной картинки коллекции
        
        if not picture_url and col.recipes:
            # Если у коллекции нет собственной картинки, берём картинку последнего рецепта
            last_recipe = col.recipes[-1]  # Последний рецепт
            picture_url = last_recipe.image_url
        
        result.append(
            CollectionBrief(
                id=col.id,
                name=col.name,
                picture_url=picture_url,
                created_at=col.created_at,
            )
        )
    return result 


@router.get("/{collection_id}", response_model=CollectionRead)
async def get_collection(collection_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Collection).where(Collection.id == collection_id))
    col: Collection | None = res.scalar()
    if col is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    recipe_ids = [r.id for r in col.recipes]
    
    # Получаем картинку последнего рецепта в коллекции
    picture_url = col.picture_url  # Начинаем с собственной картинки коллекции
    if not picture_url and col.recipes:
        # Если у коллекции нет собственной картинки, берём картинку последнего рецепта
        last_recipe = col.recipes[-1]  # Последний рецепт
        picture_url = last_recipe.image_url
    
    return CollectionRead(
        id=col.id,
        name=col.name,
        picture_url=picture_url,
        created_at=col.created_at,
        recipe_ids=recipe_ids,
    )


@router.get("/{collection_id}/recipes", response_model=List[RecipeRead])
async def get_collection_recipes(
    collection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(
        select(Recipe).join(collection_recipes).where(collection_recipes.c.collection_id == collection_id)
    )
    return res.scalars().all()


@router.post("/{collection_id}/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_recipe_to_collection(
    collection_id: uuid.UUID,
    recipe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Проверяем коллекцию и права
    res = await session.execute(select(Collection).where(Collection.id == collection_id))
    collection: Collection | None = res.scalar()
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # Проверяем рецепт
    res = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe: Recipe | None = res.scalar()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    # Добавляем связь, если ещё нет
    if recipe not in collection.recipes:
        collection.recipes.append(recipe)
        await session.commit()
    return None


@router.delete("/{collection_id}/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_recipe_from_collection(
    collection_id: uuid.UUID,
    recipe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Collection).where(Collection.id == collection_id))
    collection: Collection | None = res.scalar()
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    res = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe: Recipe | None = res.scalar()
    if recipe and recipe in collection.recipes:
        collection.recipes.remove(recipe)
        await session.commit()
    return None


# ---- Upload collection image ----


@router.post("/{collection_id}/image", response_model=CollectionRead)
async def upload_collection_image(
    collection_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Collection).where(Collection.id == collection_id))
    collection: Collection | None = res.scalar()
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # validate MIME type
    if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    # remove old image if exists and hosted locally
    if collection.picture_url and collection.picture_url.startswith(settings.MEDIA_URL):
        old_path = Path(settings.MEDIA_DIR) / collection.picture_url.replace(f"{settings.MEDIA_URL}/", "")
        if old_path.exists():
            try:
                old_path.unlink()
            except OSError:
                pass

    # save new image
    ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[file.content_type]
    filename = f"{uuid.uuid4()}{ext}"
    collections_dir = Path(settings.MEDIA_DIR) / "collections"
    collections_dir.mkdir(parents=True, exist_ok=True)
    file_path = collections_dir / filename
    with open(file_path, "wb") as buffer:
        buffer.write(data)

    collection.picture_url = f"{settings.MEDIA_URL}/collections/{filename}"
    await session.commit()
    await session.refresh(collection)

    return CollectionRead(
        id=collection.id,
        name=collection.name,
        picture_url=collection.picture_url,
        created_at=collection.created_at,
        recipe_ids=[r.id for r in collection.recipes],
    )
