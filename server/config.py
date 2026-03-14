"""
Sentry AI — Application Configuration
Loads settings from .env using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Sentry AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Demo mode — when True, enrichment clients return cached fixtures
    DEMO_MODE: bool = True

    # External API Keys
    VIRUSTOTAL_API_KEY: str = ""
    ABUSEIPDB_API_KEY: str = ""
    IPINFO_API_KEY: str = ""
    VPNAPI_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///sentry.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


settings = get_settings()
