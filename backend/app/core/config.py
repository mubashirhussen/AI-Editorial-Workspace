import os
import base64
from typing import List, Optional, Union
from pydantic import AliasChoices, Field, model_validator, field_validator
from pydantic_settings import BaseSettings

_DEFAULT_DEV_SECRET = "super-secret-editorial-ai-jwt-key-change-in-production"
_WEAK_SECRETS = {
    _DEFAULT_DEV_SECRET,
    "secret", "changeme", "admin", "password", "12345678", "editorial_secret_pass",
    "editorial_prod_master_secret_key_change_in_production_32_chars"
}

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Editorial Workspace"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./editorial.db"
    
    # Environment & Deployment Mode
    ENVIRONMENT: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "ENV"))
    TESTING: bool = Field(default=False, validation_alias=AliasChoices("TESTING", "IS_TESTING"))
    
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
    
    # Redis & Background Tasks
    REDIS_URL: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("REDIS_URL", "CELERY_BROKER_URL")
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL", "APP_LOG_LEVEL"))
    
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
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    MAX_EXTRACTION_BYTES: int = 2 * 1024 * 1024  # 2MB max download
    MAX_CONTENT_CHARS: int = 100_000             # 100k chars max article text
    EXTRACTION_TIMEOUT_SECONDS: int = 12
    MAX_REDIRECTS: int = 4
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @model_validator(mode="after")
    def validate_production_invariants(self) -> "Settings":
        if self.ENVIRONMENT.lower() in ("production", "prod"):
            # 1. Secret Key Invariants
            if self.SECRET_KEY in _WEAK_SECRETS:
                raise ValueError("In production, JWT_SECRET must be explicitly configured and cannot use default or weak secrets (cannot use the development default).")
            if len(self.SECRET_KEY) < 32:
                raise ValueError("In production, JWT_SECRET must be at least 32 characters long.")
            
            # 2. Anonymous Access Invariants
            if self.ALLOW_ANONYMOUS_DEV:
                raise ValueError("In production, ALLOW_ANONYMOUS_DEV must be set to False.")
            
            # 3. Encryption Key Validation (if set)
            if self.ENCRYPTION_KEY:
                try:
                    decoded = base64.urlsafe_b64decode(self.ENCRYPTION_KEY)
                    if len(decoded) != 32:
                        raise ValueError("ENCRYPTION_KEY must decode to exactly 32 bytes (Fernet standard).")
                except Exception as e:
                    raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")
            
            # 4. Database URL validation
            if self.DATABASE_URL.startswith("sqlite"):
                # SQLite is allowed only in dev/testing unless explicitly flagged
                pass

        return self

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()
