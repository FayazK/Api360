from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Chart Application"
    API_V1_STR: str = "/api/v1"

    # e.g: "http://localhost,http://localhost:4200,http://localhost:3000"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database settings
    DATABASE_URL: Optional[str] = None

    # JWT Token settings
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Storage Engine Settings
    STORAGE_BASE_PATH: str = "storage"
    TEMP_FILE_CLEANUP_HOURS: int = 24
    MAX_TEMP_FILE_SIZE_MB: int = 100
    
    # Legacy settings (deprecated - use storage engine)
    CHART_SAVE_DIR: str = "static/charts"
    CHART_URL_PATH: str = "/static/charts"

    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Template Settings
    TEMPLATES_DIR: str = "app/templates"
    TEMPLATE_CACHE_SIZE: int = 100

    # AI Service Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    
    # AI Service Configuration
    AI_DEFAULT_PROVIDER: str = "openai"
    AI_DEFAULT_MODEL: Optional[str] = None
    AI_MAX_TOKENS_DEFAULT: int = 1000
    AI_TEMPERATURE_DEFAULT: float = 0.7
    AI_REQUEST_TIMEOUT: int = 60  # seconds

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()