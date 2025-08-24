import json, asyncio, os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.tag import Tag

# подключение
engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def main():
    tags = json.load(open("utils/extracted_tags.json", encoding="utf-8"))
    async with AsyncSessionLocal() as session:
        added = 0
        for name in tags:
            res = await session.execute(select(Tag).where(Tag.name == name))
            if res.scalar():
                continue
            session.add(Tag(name=name))
            added += 1
        await session.commit()
    print(f"Added {added} tags")

if __name__ == "__main__":
    asyncio.run(main())