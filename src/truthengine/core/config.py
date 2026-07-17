"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Typed application settings sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TRUTHENGINE_",
        extra="ignore",
    )

    environment: Environment = Field(default="local", description="Runtime environment name.")
    service_name: str = Field(default="truthengine-api", description="Service name for logs.")
    app_version: str = Field(default="0.1.0", description="Application version string.")
    log_level: LogLevel = Field(default="INFO", description="Minimum log level.")
    log_json: bool = Field(default=True, description="Emit logs as JSON when true.")
    request_id_header: str = Field(
        default="X-Request-ID",
        description="HTTP header used to receive and return request correlation IDs.",
    )
    database_url: str = Field(
        default="postgresql+psycopg://truthengine:truthengine@localhost:5432/truthengine",
        description="SQLAlchemy database URL for the application database.",
    )

    # SearXNG search provider
    searxng_url: str = Field(
        default="http://localhost:8888",
        description="Base URL of the SearXNG instance used for web search.",
    )
    searxng_max_results: int = Field(
        default=6,
        description="Maximum number of search results to request per query.",
    )

    # DeepSeek LLM provider
    deepseek_api_key: str = Field(
        default="",
        description="DeepSeek API key. Leave empty to disable LLM stages.",
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        description="DeepSeek model identifier.",
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        description="Base URL for the DeepSeek API (OpenAI-compatible).",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://frontend:5173"],
        description="Allowed CORS origins for the frontend.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings for process-wide reuse."""
    return Settings()
