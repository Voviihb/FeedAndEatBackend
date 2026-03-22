from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.recipe import Recipe
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter()


async def _recalc_rating(recipe_id: uuid.UUID, session: AsyncSession) -> None:
    """Пересчитывает рейтинг рецепта как среднее всех отзывов."""
    result = await session.execute(
        select(func.avg(Review.mark)).where(Review.recipe_id == recipe_id)
    )
    avg_mark: Optional[float] = result.scalar()

    res = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe: Optional[Recipe] = res.scalar()
    if recipe is not None:
        recipe.rating = round(avg_mark, 2) if avg_mark is not None else 0.0
        await session.commit()


@router.get("/{recipe_id}/reviews", response_model=List[ReviewRead])
async def get_recipe_reviews(
    recipe_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Получить все отзывы на рецепт."""
    res = await session.execute(
        select(Review).where(Review.recipe_id == recipe_id)
    )
    return res.scalars().all()


@router.get("/{recipe_id}/reviews/my", response_model=Optional[ReviewRead])
async def get_my_review(
    recipe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить свой отзыв на рецепт (или null если не оставлял)."""
    res = await session.execute(
        select(Review).where(
            Review.recipe_id == recipe_id,
            Review.user_id == current_user.id
        )
    )
    return res.scalar()


@router.post(
    "/{recipe_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_review(
    recipe_id: uuid.UUID,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Добавить отзыв на рецепт. Один пользователь — один отзыв."""
    # Проверяем, что рецепт существует
    res = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe: Optional[Recipe] = res.scalar()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Проверяем, не оставлял ли пользователь уже отзыв
    existing = await session.execute(
        select(Review).where(
            Review.recipe_id == recipe_id,
            Review.user_id == current_user.id
        )
    )
    if existing.scalar() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this recipe. Use PUT to update."
        )

    review = Review(
        recipe_id=recipe_id,
        user_id=current_user.id,
        mark=data.mark,
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)

    # Пересчитываем рейтинг рецепта
    await _recalc_rating(recipe_id, session)

    return review


@router.put("/{recipe_id}/reviews/my", response_model=ReviewRead)
async def update_my_review(
    recipe_id: uuid.UUID,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Обновить свой отзыв на рецепт."""
    res = await session.execute(
        select(Review).where(
            Review.recipe_id == recipe_id,
            Review.user_id == current_user.id
        )
    )
    review: Optional[Review] = res.scalar()

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found. Use POST to create a new review."
        )

    review.mark = data.mark
    await session.commit()
    await session.refresh(review)

    # Пересчитываем рейтинг рецепта
    await _recalc_rating(recipe_id, session)

    return review


@router.delete("/{recipe_id}/reviews/my", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_review(
    recipe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удалить свой отзыв на рецепт."""
    res = await session.execute(
        select(Review).where(
            Review.recipe_id == recipe_id,
            Review.user_id == current_user.id
        )
    )
    review: Optional[Review] = res.scalar()

    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    await session.delete(review)
    await session.commit()

    # Пересчитываем рейтинг рецепта
    await _recalc_rating(recipe_id, session)

    return None
