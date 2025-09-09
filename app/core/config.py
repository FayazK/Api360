from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Union
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Chart Application"
    API_V1_STR: str = "/api/v1"

    # Can be CSV string or list in env: "http://localhost,http://localhost:4200"
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
    # Google GenAI (alternative to GEMINI_API_KEY) and Vertex flags
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_GENAI_USE_VERTEXAI: bool = False
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: Optional[str] = None
    
    # Replicate SDK token
    REPLICATE_API_TOKEN: Optional[str] = None
    
    # AI Service Configuration
    AI_DEFAULT_PROVIDER: str = "openai"
    AI_DEFAULT_MODEL: Optional[str] = None
    AI_MAX_TOKENS_DEFAULT: int = 1000
    AI_TEMPERATURE_DEFAULT: float = 0.7
    AI_REQUEST_TIMEOUT: int = 60  # seconds
    
    # Image generation defaults (leave empty to require explicit provider)
    IMAGE_DEFAULT_PROVIDER: Optional[str] = None
    IMAGE_DEFAULT_MODEL: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]):
        """Allow CORS origins to be provided as a CSV string or list.
        If empty or missing, return an empty list.
        """
        if v is None or v == "":
            return []
        if isinstance(v, str):
            # Split CSV, strip spaces, drop empties
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts
        if isinstance(v, list):
            return v
        return []


settings = Settings()
