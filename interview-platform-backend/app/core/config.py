import os
from pydantic_settings import BaseSettings
from typing import Any, Dict, List, Optional, Union

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Interview Platform"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000","*"]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "interview_platform")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    ASYNC_SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    
    # WebRTC
    STUN_SERVERS: List[str] = ["stun:stun.l.google.com:19302"]
    TURN_SERVERS: List[Dict[str, Any]] = []
    
    # DeepFace
    DEEPFACE_MODEL: str = "VGG-Face"
    SPOOFING_DETECTION_INTERVAL: int = 5  # seconds
    
    class Config:
        case_sensitive = True
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Support both connection methods
        if self.DATABASE_URL:
            from urllib.parse import urlparse
            parsed_url = urlparse(self.DATABASE_URL)
            self.ASYNC_SQLALCHEMY_DATABASE_URI = f"postgresql+asyncpg://{parsed_url.username}:{parsed_url.password}@{parsed_url.hostname}{parsed_url.path}?ssl=require"
            self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        else:
            self.SQLALCHEMY_DATABASE_URI = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            self.ASYNC_SQLALCHEMY_DATABASE_URI = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"


settings = Settings()