from fastapi import FastAPI

from app.api import auth
from app.core.database import engine, Base

app = FastAPI(title="FeedAndEat API")

# Подключаем все модули
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
