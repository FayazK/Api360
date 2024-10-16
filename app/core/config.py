from pydantic import BaseSettings, AnyHttpUrl
from typing import List, Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Chart Application"
    API_V1_STR: str = "/api/v1"

    # BACKEND_CORS_ORIGINS is a comma-separated list of origins
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

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()