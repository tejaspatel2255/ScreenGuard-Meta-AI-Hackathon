from typing import List, Literal, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROVIDER: str = "meta"
    META_API_KEY: str = ""
    META_API_BASE_URL: str = "https://api.meta.ai/v1"
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_VISION_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_TEXT_MODEL: str = "openai/gpt-oss-120b"
    BASETEN_API_KEY: str = ""
    BASETEN_MODEL: str = "meta-models/muse-spark-open-1026"
    MODE: Literal["mock", "real", "replay"] = "mock"
    USE_SAM: bool = False
    USE_VOICE: bool = False
    MAX_CALLS_PER_SESSION: int = 300
    MAX_CALLS_PER_MINUTE: int = 20
    MAX_ESTIMATED_SPEND_USD: float = 100.0
    CONFIDENCE_ADVANCE: float = 0.7
    CONFIDENCE_HIGH_RISK: float = 0.85
    WARNING_COOLDOWN_SECONDS: int = 8
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]


settings = Settings()
