"""Application configuration sourced from environment variables."""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings for local and Azure-hosted environments."""

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    sql_connection_string: SecretStr = Field(alias="SQL_CONNECTION_STRING")
    default_bonus_rate: Decimal = Field(default=Decimal("0.05"), alias="DEFAULT_BONUS_RATE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_page_size: int = Field(default=200, alias="MAX_PAGE_SIZE", ge=1, le=1000)
    applicationinsights_connection_string: str | None = Field(
        default=None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance for the process lifetime."""
    return Settings()  # type: ignore[call-arg]
