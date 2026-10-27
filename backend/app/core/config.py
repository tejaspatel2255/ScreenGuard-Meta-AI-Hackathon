from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROVIDER: str = "meta"
    META_API_KEY: str = ""
    META_API_BASE_URL: str = ""
    BASETEN_API_KEY: str = ""
    BASETEN_MODEL: str = "meta-models/muse-spark-open-1026"
    MODE: Literal["mock", "real", "replay"] = "mock"
    USE_SAM: bool = True
    USE_VOICE: bool = False
    MAX_CALLS_PER_SESSION: int = 60
    MAX_CALLS_PER_MINUTE: int = 10
    MAX_ESTIMATED_SPEND_USD: float = 100.0
    CONFIDENCE_ADVANCE: float = 0.7
    CONFIDENCE_HIGH_RISK: float = 0.85
    WARNING_COOLDOWN_SECONDS: int = 8


settings = Settings()
