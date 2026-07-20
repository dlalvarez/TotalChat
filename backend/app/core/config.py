from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "dev"
    service_name: str = "totalchat-api"
    database_url: str | None = None
    admin_cors_origins: str = 'http://127.0.0.1:5173,http://localhost:5173'
    jwt_secret: str | None = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    embeddings_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TOTALCHAT_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
