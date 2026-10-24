"""
Configuration Management
Centralized settings loaded from environment variables
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    Usage:
        from backend.utils.config import settings
        api_key = settings.gemini_api_key
    """
    
    # Application
    app_name: str = "Sanctuary"
    app_version: str = "1.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # API Keys
    gemini_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    allow_credentials: bool = True
    
    # Gemini Configuration
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 500
    
    # Voice Configuration
    elevenlabs_voice: str = "Rachel"
    elevenlabs_model: str = "eleven_turbo_v2"
    whisper_model: str = "whisper-1"
    
    # Session Configuration
    session_expiry_hours: int = 24
    max_conversation_turns: int = 100
    
    # Rate Limiting
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 60
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
