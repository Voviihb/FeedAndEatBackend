import json, asyncio, uuid, os
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings       # берёт данные из .env
from app.models.recipe import Recipe
from app.models.user import User
import app.models.collection
from app.core.database import Base

# --- подключаемся к Postgres ---------------------------------
engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# --- ID «системного» пользователя для импортированных рецептов
SYSTEM_EMAIL = os.getenv("SYSTEM_EMAIL", "admin@google.com")
SYSTEM_USERNAME = os.getenv("SYSTEM_USERNAME", "admin")
SYSTEM_PASSWORD = os.getenv("SYSTEM_PASSWORD", "admin")

async def get_or_create_system_user(session):
    res = await session.execute(select(User).where(User.email == SYSTEM_EMAIL))
    user = res.scalar()
    if user:
        return user.id
    user = User(email=SYSTEM_EMAIL, username=SYSTEM_USERNAME, hashed_password=SYSTEM_PASSWORD)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user.id

# --- чтение и вставка -----------------------------------------
async def main():
    async with AsyncSessionLocal() as session:
        system_user_id = await get_or_create_system_user(session)

        data = json.load(open("utils/recipes_russian.json", "r", encoding="utf-8"))
        counter = 0
        for rec in data:
            recipe = Recipe(
                id=uuid.uuid4(),
                user_id=system_user_id,
                name=rec["name"],
                image_url=rec.get("image"),
                instructions=rec.get("instructions", []),
                servings=rec.get("servings"),
                ingredients=rec.get("ingredients", []),
                tags=rec.get("tags", []),
                nutrients=rec.get("nutrients"),
                rating=float(rec.get("rating", 0)),
                cooked=int(rec.get("cooked", 0)),
                created_at=datetime.utcnow(),
            )
            session.add(recipe)
            counter += 1

            # пачками по 500 – быстрее
            if counter % 500 == 0:
                await session.commit()
                print(f"Inserted {counter}")

        await session.commit()
        print(f"Done! Inserted total {counter} recipes")

if __name__ == "__main__":
    asyncio.run(main())