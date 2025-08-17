import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth
from app.core.database import engine, Base
from app.core.config import settings

app = FastAPI(title="FeedAndEat API")

# CORS — разрешаем мобильному клиенту делать запросы
origins = ["*"]  # при необходимости заменить на конкретный список
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем все модули
app.include_router(auth.router, prefix="/auth", tags=["auth"])
from app.api import users as users_router
from app.api import recipes as recipes_router
app.include_router(users_router.router, prefix="/users", tags=["users"])
app.include_router(recipes_router.router, prefix="/recipes", tags=["recipes"])
from app.api import collections as collections_router
app.include_router(collections_router.router, prefix="/collections", tags=["collections"])
from app.api import tags as tags_router
app.include_router(tags_router.router, prefix="/tags", tags=["tags"])
from app.api import devices as devices_router
app.include_router(devices_router.router, prefix="/devices", tags=["devices"])

# Статика для загруженных медиа (аватары и др.)
media_path = Path(settings.MEDIA_DIR)
media_path.mkdir(parents=True, exist_ok=True)
app.mount(settings.MEDIA_URL, StaticFiles(directory=str(media_path)), name="media")

# Media dirs only (создание таблиц теперь исключительно через Alembic)
@app.on_event("startup")
async def on_startup():
    (media_path / "avatars").mkdir(parents=True, exist_ok=True)
    (media_path / "recipes").mkdir(parents=True, exist_ok=True)
    (media_path / "collections").mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
