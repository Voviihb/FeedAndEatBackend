# Pydantic v2: BaseSettings вынесен в отдельный пакет
from pydantic_settings import BaseSettings
# Настройки читаются из переменных окружения или из файла .env автоматически.


class Settings(BaseSettings):
    """Глобальные настройки для приложения."""

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "feedandeat"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    SECRET_KEY: str = "supersecret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    MEDIA_DIR: str = "media"
    MEDIA_URL: str = "/media"

    class Config:
        env_file = ".env"
        extra = "allow"
        env_file_encoding = "utf-8"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings() 