# FeedAndEat Backend

Бэкенд для мобильного приложения FeedAndEat (FastAPI + PostgreSQL).

## Быстрый старт

```bash
# 1. Создать и активировать виртуальное окружение
python -m venv venv
source venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Скопировать пример .env файла в .env (в корне проекта) 
# и при необходимости поменять значения
cp .env.example .env

# 4. Запустить Postgres (локально или через docker)

# 5. Применить миграции
alembic upgrade head

# 6. Запустить сервер
uvicorn main:app --reload
```

API документация доступна по адресу: http://localhost:8000/docs

## Переменные окружения (.env)

```ini
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=feedandeat
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT
SECRET_KEY=supersecret
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Медиа файлы
MEDIA_DIR=media
MEDIA_URL=/media

# CORS
ALLOWED_ORIGINS=*  # список через запятую или *
```

## Разработка
* Схему БД меняем только через Alembic (`alembic revision --autogenerate -m "..."`).
* При запуске создаются папки `media/avatars`, `media/recipes`, `media/collections`.
* Для быстрого поиска используется расширение `pg_trgm`. 