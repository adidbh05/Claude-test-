"""
Application Settings and Configuration.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Eurocode 3 Structural Design Chat"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM Configuration
    use_mock_llm: bool = True
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    llm_model: Optional[str] = None

    # Rate Limiting
    rate_limit_per_minute: int = 30
    rate_limit_per_hour: int = 500

    # Database
    db_path: str = "conversations.db"

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    backend_dir: Path = base_dir / "backend"
    frontend_dir: Path = base_dir / "frontend"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
