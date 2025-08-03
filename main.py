import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import auth
from app.core.database import engine, Base
from app.core.config import settings

app = FastAPI(title="FeedAndEat API")

# Подключаем все модули
app.include_router(auth.router, prefix="/auth", tags=["auth"])
from app.api import users as users_router
app.include_router(users_router.router, prefix="/users", tags=["users"])

# Статика для загруженных медиа (аватары и др.)
media_path = Path(settings.MEDIA_DIR)
media_path.mkdir(parents=True, exist_ok=True)
app.mount(settings.MEDIA_URL, StaticFiles(directory=str(media_path)), name="media")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # убеждаемся, что директория под аватары существует
    (media_path / "avatars").mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
