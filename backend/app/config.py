"""
Application configuration settings.

Uses pydantic-settings to load configuration from environment variables.
"""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "KidSafe AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database (required - must be set via environment variable or .env file)
    DATABASE_URL: str

    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""

    # Gemini Configuration
    GEMINI_API_KEY: str = ""

    # AI Provider Selection (openai, gemini, or auto)
    AI_PROVIDER: str = "auto"

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
