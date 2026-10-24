import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    # Database (Zone A)
    DATABASE_URL: str = "sqlite+aiosqlite:///./sanctuary.db"
    REDIS_URL: str = "redis://localhost:6379"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # Zone C Providers (Replaceable - Dependency Inversion)
    LLM_PROVIDER: str = "groq"            # Options: groq, ollama, vllm
    TTS_PROVIDER: str = "elevenlabs"      # Options: elevenlabs, piper, xttsv2
    STT_PROVIDER: str = "whisper_cloud"   # Options: whisper_cloud, faster_whisper

    # External APIs (Zone C only)
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = None

    # UKF Configuration
    UKF_PROCESS_NOISE: float = 0.01
    UKF_OBSERVATION_NOISE: float = 0.1
    UKF_ALPHA: float = 0.001
    UKF_BETA: float = 2.0
    UKF_KAPPA: float = 0.0

settings = Settings()
