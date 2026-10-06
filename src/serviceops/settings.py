from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SERVICEOPS_", env_file=".env", extra="ignore")

    env: str = "development"
    demo_mode: bool = True
    database_url: str = "postgresql+psycopg://serviceops:serviceops@localhost:5432/serviceops"
    operations_url: str = "http://localhost:8081"
    operations_token: str = Field(default="local-sandbox-token", repr=False)
    session_secret: str = Field(default="local-development-only-change-me", repr=False)
    webhook_secret: str = Field(default="local-webhook-only-change-me", repr=False)
    business_timezone: str = "America/Manaus"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = ""
    integration_route: str = "direct"
    inject_drop_after_commit: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
