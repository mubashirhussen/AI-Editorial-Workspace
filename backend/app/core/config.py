import os
from typing import List, Optional
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings

_DEFAULT_DEV_SECRET = "super-secret-editorial-ai-jwt-key-change-in-production"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Editorial Workspace"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./editorial.db"
    
    # Environment & Deployment Mode
    ENVIRONMENT: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "ENV"))
    
    # Authentication & Security
    SECRET_KEY: str = Field(
        default=_DEFAULT_DEV_SECRET,
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY")
    )
    ENCRYPTION_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ENCRYPTION_KEY", "APP_ENCRYPTION_KEY")
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALLOW_ANONYMOUS_DEV: bool = True  # Backward compatibility for local development & legacy tests
    
    # Modular AI Providers
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Backward compatibility AI settings
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    
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
    MAX_EXTRACTION_BYTES: int = 2 * 1024 * 1024  # 2MB max download
    MAX_CONTENT_CHARS: int = 100_000             # 100k chars max article text
    EXTRACTION_TIMEOUT_SECONDS: int = 12
    MAX_REDIRECTS: int = 4
    
    @model_validator(mode="after")
    def validate_production_invariants(self) -> "Settings":
        if self.ENVIRONMENT.lower() in ("production", "prod"):
            if self.SECRET_KEY == _DEFAULT_DEV_SECRET:
                raise ValueError("In production, JWT_SECRET must be explicitly configured and cannot use the development default.")
            if len(self.SECRET_KEY) < 32:
                raise ValueError("In production, JWT_SECRET must be at least 32 characters long.")
            if self.ALLOW_ANONYMOUS_DEV:
                raise ValueError("In production, ALLOW_ANONYMOUS_DEV must be set to False.")
        return self

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()
