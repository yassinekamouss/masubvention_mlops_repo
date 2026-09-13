import os
from typing import Optional


class Settings:
    """Application configuration loaded from environment variables."""

    # App
    PROJECT_NAME: str = "Masubvention MLOps Pipeline — Le Consultant Virtuel"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Webhook Integration
    EXPRESS_WEBHOOK_URL: str = os.getenv(
        "EXPRESS_WEBHOOK_URL",
        "http://localhost:5000/api/internal/webhook/dossier-completed"
    )
    WEBHOOK_TIMEOUT_SECONDS: float = float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "15.0"))

    # LLM Settings
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))


settings = Settings()
