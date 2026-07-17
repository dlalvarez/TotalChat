from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "dev"
    service_name: str = "totalchat-api"
    database_url: str | None = None
    admin_cors_origins: str = 'http://127.0.0.1:5173,http://localhost:5173'
    jwt_secret: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TOTALCHAT_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
