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

    # Chart settings
    CHART_SAVE_DIR: str = "static/charts"
    CHART_URL_PATH: str = "/static/charts"

    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Template Settings
    TEMPLATES_DIR: str = "app/templates"
    TEMPLATE_CACHE_SIZE: int = 100

    # AI Settings
    OPENAI_API_KEY: str = None
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()