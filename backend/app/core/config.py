from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "dev"
    service_name: str = "totalchat-api"
    database_url: str | None = None
    admin_cors_origins: str = 'http://127.0.0.1:5173,http://localhost:5173'
    jwt_secret: str | None = None
    llm_provider: str = "openai"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30
    embeddings_provider: str | None = None
    embeddings_base_url: str | None = None
    embeddings_api_key: str | None = None
    openai_api_key: str | None = None
    embeddings_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    @property
    def effective_llm_api_key(self) -> str | None:
        """Use the deprecated OpenAI key only for the OpenAI adapter."""
        if self.llm_api_key:
            return self.llm_api_key
        if self.llm_provider.lower() == "openai":
            return self.openai_api_key
        return None

    @property
    def effective_embeddings_provider(self) -> str:
        return self.embeddings_provider or self.llm_provider

    @property
    def effective_embeddings_base_url(self) -> str:
        return self.embeddings_base_url or self.llm_base_url

    @property
    def effective_embeddings_api_key(self) -> str | None:
        if self.embeddings_api_key:
            return self.embeddings_api_key
        if self.llm_api_key:
            return self.llm_api_key
        if self.effective_embeddings_provider.lower() == "openai" and self.llm_provider.lower() == "openai":
            return self.openai_api_key
        return None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TOTALCHAT_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
