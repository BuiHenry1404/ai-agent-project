import os
from typing import List


class Settings:
    """Application settings"""
    
    # Project info
    PROJECT_NAME: str = "Agent Training Course API"
    PROJECT_DESCRIPTION: str = "FastAPI application with autogen agents for study planning and life advice"
    PROJECT_VERSION: str = "1.0.0"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SWAGGER_PATH: str = ""
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    # Authentication (optional)
    ORIGIN_HEADER: str = os.getenv("ORIGIN_HEADER", "")
    
    # LLM settings (Gemini only)
    DEFAULT_LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Task settings
    DEFAULT_MAX_TURNS: int = int(os.getenv("DEFAULT_MAX_TURNS", "10"))
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"


# Global settings instance
settings = Settings()
