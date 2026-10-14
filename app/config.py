from functools import lru_cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: HttpUrl | None = None
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_transcribe_model: str = "gpt-4o-transcribe"
    openai_decisions_model: str = "gpt-6-luna-openai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
