import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Editorial Workspace"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./editorial.db"
    
    # Authentication & Multi-Tenancy
    SECRET_KEY: str = os.getenv("JWT_SECRET", "super-secret-editorial-ai-jwt-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALLOW_ANONYMOUS_DEV: bool = True  # Backward compatibility for single-user dev & existing tests
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o-mini"
    
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
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()

