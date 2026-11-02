import os
from typing import List, Optional

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings


_DEVELOPMENT_SECRET_KEY = "super-secret-editorial-ai-jwt-key-change-in-production"


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Editorial Workspace"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./editorial.db"

    # Authentication & Security.
    # JWT_SECRET is the canonical name; SECRET_KEY remains as a compatibility alias.
    SECRET_KEY: str = Field(
        default=_DEVELOPMENT_SECRET_KEY,
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"),
    )
    ENVIRONMENT: str = "development"
    ENCRYPTION_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALLOW_ANONYMOUS_DEV: bool = True

    # Modular AI Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_AI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Backward compatibility AI settings
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o-mini"

    DEFAULT_AI_PROVIDER: str = "groq"
    DEFAULT_AI_MODEL: str = "openai/gpt-oss-20b"

    # Security & Extraction Settings
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    MAX_EXTRACTION_BYTES: int = 2 * 1024 * 1024
    MAX_CONTENT_CHARS: int = 100_000
    EXTRACTION_TIMEOUT_SECONDS: int = 12
    MAX_REDIRECTS: int = 4

    @model_validator(mode="after")
    def require_secure_production_secret(self):
        if self.ENVIRONMENT.strip().lower() == "production":
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == _DEVELOPMENT_SECRET_KEY
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "Production requires JWT_SECRET (or legacy SECRET_KEY) "
                    "with at least 32 characters. Do not use the development default."
                )
        return self

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
        "populate_by_name": True,
    }


settings = Settings()
