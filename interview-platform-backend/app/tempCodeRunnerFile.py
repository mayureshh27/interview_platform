from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
import asyncio

from app.api.endpoints import auth, interviews, users, websocket
from app.core.config import settings
from app.db.session import engine, async_engine
from app.models.base import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables (using synchronous engine for setup)
Base.metadata.create_all(bind=engine)

# Create recordings directory if it doesn't exist
os.makedirs("recordings", exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(interviews.router, prefix=f"{settings.API_V1_STR}/interviews", tags=["interviews"])
app.include_router(websocket.router, tags=["websocket"])

# Serve static files (recordings)
app.mount("/recordings", StaticFiles(directory="recordings"), name="recordings")

@app.on_event("startup")
async def startup_db_connection():
    """Verify database connection on startup"""
    try:
        # Test async connection
        from sqlalchemy import text
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await conn.commit()
            logger.info("Successfully connected to Neon PostgreSQL database")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_connection():
    """Close database connections"""
    await asyncio.shield(async_engine.dispose())
    logger.info("Database connections closed")

@app.get("/")
def root():
    return {"message": "Welcome to the Interview Platform API"}

@app.get("/health")
async def health_check():
    from sqlalchemy import text
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        await conn.commit()
    return {"status": "healthy", "database": "connected"}   