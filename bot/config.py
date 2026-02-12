from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    telegram_bot_token: str
    initial_admin_id: int

    # Monitoring
    health_check_interval: int = 60
    notification_cooldown: int = 300

    # Database
    database_url: str = "sqlite+aiosqlite:///data/bot.db"

    # vLLM
    vllm_api_url: str = "http://localhost:8001/v1"

    # Jira
    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project: str = "DOCS"

    # Paths
    cycle_runner_lock_path: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
