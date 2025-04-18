# app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Interview Platform"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS
    # WARNING: Allowing "*" is NOT recommended for production due to security risks.
    # Restrict to known frontend origins (e.g., "https://yourfrontend.com")
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000","*"] # Added warning comment

    # Database - Neon PostgreSQL connection
    # DATABASE_URL should be the standard postgresql://... string provided by Neon
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    # SQLALCHEMY_DATABASE_URI will hold the URL for the synchronous engine (same as DATABASE_URL)
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    # ASYNC_SQLALCHEMY_DATABASE_URI will hold the URL for the asynchronous engine (postgresql+asyncpg://...)
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

        # Parse and configure Neon PostgreSQL connection
        if not self.DATABASE_URL:
             raise ValueError("DATABASE_URL environment variable is required for database connection") # Raised if empty string default is used

        # Use the connection string exactly as provided by Neon for the synchronous engine
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL

        # For the async connection, parse and create a properly formatted URL
        parsed_url = urlparse(self.DATABASE_URL)
        username = unquote(parsed_url.username) if parsed_url.username else ""
        password = unquote(parsed_url.password) if parsed_url.password else ""
        hostname = parsed_url.hostname
        path = unquote(parsed_url.path) if parsed_url.path else ""

        # Construct the async URL using the postgresql+asyncpg dialect and include the necessary SSL parameter
        # Use ssl=require which is commonly understood by asyncpg via SQLAlchemy
        query_params = parsed_url.query # Preserve existing query parameters if any
        if query_params:
             self.ASYNC_SQLALCHEMY_DATABASE_URI = f"postgresql+asyncpg://{username}:{password}@{hostname}{path}?{query_params}&ssl=require"
        else:
             self.ASYNC_SQLALCHEMY_DATABASE_URI = f"postgresql+asyncpg://{username}:{password}@{hostname}{path}?ssl=require"


settings = Settings()