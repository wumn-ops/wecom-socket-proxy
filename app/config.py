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

    upload_token_secret: str = ""

    smartsheet_webhook_url: str = ""
    smartsheet_field_demand_content: str = "f9VtuW"
    smartsheet_field_image: str = "fhZuXt"
    smartsheet_field_submitter: str = "f04Gwj"
    issue_list_url: str = ""

    public_base_url: str = ""
    register_upload_path: str = "/register/upload"
    upload_token_ttl_seconds: int = 3600
    max_upload_bytes: int = 5 * 1024 * 1024

    wecom_corp_id: str = ""
    wecom_agent_id: str = ""
    wecom_corp_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
