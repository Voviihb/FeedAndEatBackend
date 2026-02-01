import asyncio
import json
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, text
from app.core.config import settings

# Импортируем все модели
from app.models.user import User
from app.models.recipe import Recipe
from app.models.collection import Collection
from app.models.daily_recipe import DailyRecipe
from app.models.device_token import DeviceToken
from app.models.tag import Tag

# Подключение к БД
engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Системный пользователь
SYSTEM_EMAIL = "admin@google.com"
SYSTEM_USERNAME = "admin"


async def fix_timer_data_in_json(instructions):
    """Правильно обрабатывает таймеры - ТОЛЬКО добавляет ID, НЕ МЕНЯЯ оригинальные данные"""
    for instruction in instructions:
        timers = instruction.get('timers', [])
        for timer in timers:
            # ТОЛЬКО добавляем ID если его нет, остальное НЕ ТРОГАЕМ!
            if 'id' not in timer:
                timer['id'] = str(uuid.uuid4())
            
            # Добавляем алиасы для совместимости, но СОХРАНЯЕМ оригинальные поля
            if 'lowerLimit' in timer and 'lower_limit' not in timer:
                timer['lower_limit'] = timer['lowerLimit']
            
            if 'upperLimit' in timer and 'upper_limit' not in timer:
                timer['upper_limit'] = timer['upperLimit']
    
    return instructions


async def get_or_create_system_user(session):
    """Получает или создает системного пользователя"""
    result = await session.execute(select(User).where(User.email == SYSTEM_EMAIL))
    user = result.scalar()
    if user:
        return user.id
    
    user = User(
        email=SYSTEM_EMAIL, 
        username=SYSTEM_USERNAME, 
        hashed_password="$2b$12$dummy_hash"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user.id


async def reimport_recipes():
    """Переимпортирует рецепты с правильной обработкой таймеров"""
    async with AsyncSessionLocal() as session:
        print("🧹 Очищаем таблицу рецептов...")
        await session.execute(text("DELETE FROM recipes"))
        await session.commit()
        
        print("👤 Создаем системного пользователя...")
        system_user_id = await get_or_create_system_user(session)
        
        print("📖 Загружаем данные из JSON...")
        data = json.load(open("utils/recipes_russian.json", "r", encoding="utf-8"))
        
        print(f"🔄 Импортируем {len(data)} рецептов с правильной обработкой таймеров...")
        
        counter = 0
        for rec in data:
            # Обрабатываем инструкции и таймеры ПРАВИЛЬНО
            instructions = await fix_timer_data_in_json(rec.get("instructions", []))
            
            recipe = Recipe(
                id=uuid.uuid4(),
                user_id=system_user_id,
                name=rec["name"],
                image_url=rec.get("image"),
                instructions=instructions,  # ← Правильно обработанные инструкции
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

            # Коммитим пачками
            if counter % 500 == 0:
                await session.commit()
                print(f"✅ Импортировано {counter} рецептов...")

        await session.commit()
        print(f"🎉 Завершено! Импортировано {counter} рецептов с правильными таймерами!")
        
        # Проверяем результат
        print("\n🔍 Проверяем несколько таймеров:")
        result = await session.execute(
            text("SELECT name, instructions::text FROM recipes WHERE instructions::text LIKE '%timer%' LIMIT 3")
        )
        for row in result.fetchall():
            print(f"  {row[0]}: {row[1][:200]}...")


if __name__ == "__main__":
    asyncio.run(reimport_recipes())