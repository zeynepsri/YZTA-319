from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Uygulama ayarları."""

    
    APP_NAME: str = "Kişisel Enflasyon API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True


    DATABASE_URL: str = "sqlite:///./enflasyon.db"


    SECRET_KEY: str = "enflasyon-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


    GEMINI_API_KEY: Optional[str] = None

    
    GEMINI_MODEL: str = "gemini-2.5-flash"

    
    REDIS_URL: Optional[str] = None


  
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10


  
    CORS_ORIGINS: list[str] = ["*"]


    class Config:
        env_file = ".env"
        case_sensitive = True



@lru_cache()
def get_settings() -> Settings:
    return Settings()



settings = get_settings()



os.makedirs(settings.UPLOAD_DIR, exist_ok=True)