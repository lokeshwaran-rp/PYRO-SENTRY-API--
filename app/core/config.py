"""
PYRO-SENTRY application configuration.
Reads from environment variables with sensible defaults for local development.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # General
    PROJECT_NAME: str = "PYRO-SENTRY Industrial Thermal Surveillance API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://pyro:pyro@localhost:5432/pyrosentry"
    # For tests, override with: sqlite+aiosqlite:///
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CHANNEL: str = "pyrosentry:events"

    # JWT
    PYRO_JWT_SECRET: str = "changeme-in-production-use-openssl-rand-hex-32"
    PYRO_JWT_ALGORITHM: str = "HS256"
    PYRO_JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PYRO_JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
