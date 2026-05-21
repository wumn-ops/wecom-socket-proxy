from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    wecom_bot_id: str = ""
    wecom_bot_secret: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    wecom_callback_path: str = "/wecom/aibot/callback"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
