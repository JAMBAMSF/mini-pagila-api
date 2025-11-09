from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mini Pagila API"
    environment: Literal["local", "test", "prod"] = "local"
    database_url: str = Field(validation_alias="DATABASE_URL")
    admin_bearer_token: str = Field(default="dvd_admin", validation_alias="ADMIN_BEARER_TOKEN")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    log_json: bool = Field(default=False, validation_alias="LOG_JSON")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()                          
