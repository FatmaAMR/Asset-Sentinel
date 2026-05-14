from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Configurations
    PROJECT_NAME: str = "Sentinel AI - Querying Service"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./shared.db"
    
    # Internal Services URLs
    MASTER_LLM_SERVICE_URL: str = "http://localhost:8005"   # legacy / mock
    MASTER_LLM_URL: str = "http://localhost:8000"            # master-llm-service /generate
    MASTER_LLM_ADMIN_KEY: str = "gradteam"                  # X-Admin-Key for /admin/*
    CONSULTING_SERVICE_URL: str = "http://localhost:8001"
    MANAGERIAL_SERVICE_URL: str = "http://localhost:8002"
    
    # External API Keys (For the Mock Master)
    GROQ_API_KEY: Optional[str] = None
    USE_MOCK_MASTER: bool = True

    # Pydantic Config to load from .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # This prevents errors if extra fields are in .env
    )

# Create a singleton instance
settings = Settings()