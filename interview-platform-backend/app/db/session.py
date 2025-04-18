# app/db/session.py
from sqlalchemy import create_engine # For synchronous engine
from sqlalchemy.orm import sessionmaker # For synchronous sessionmaker

# Import asynchronous components
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# Correct import for asynchronous sessionmaker
from sqlalchemy.ext.asyncio.session import async_sessionmaker # <-- Correct import

from app.core.config import settings
# Use the existing Base class from base_class.py
from app.db.base_class import Base


# --- Synchronous Engine and Session ---
# Used if you need synchronous database operations (less common in FastAPI)
# Uses the raw DATABASE_URL (e.g., postgresql://...)
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True
    # Add connect_args if your synchronous driver also needs specific SSL config
    # For standard 'psycopg2' used by 'postgresql://', sslmode can often be in the URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for synchronous operations
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Asynchronous Engine and Session ---
# Used for asynchronous database operations (standard in FastAPI)
# Uses the ASYNC_SQLALCHEMY_DATABASE_URI (e.g., postgresql+asyncpg://... with ?ssl=require)
async_engine = create_async_engine(
    settings.ASYNC_SQLALCHEMY_DATABASE_URI,
    echo=False, # Set to True to see SQL queries
    future=True, # Recommended for SQLAlchemy 2.0 style
    pool_pre_ping=True
    # Note: ssl=require is included in the URL by config.py,
    # so connect_args={'ssl': 'require'} is NOT needed here unless
    # you remove it from the URL construction in config.py
)

# Correct way to create an asynchronous sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, # Use bind=
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for asynchronous operations (use this in your async API endpoints)
async def get_async_db() -> AsyncSession:
    # The async with statement properly manages the session's lifecycle
    async with AsyncSessionLocal() as session:
        yield session
    # The async with block automatically calls await session.close() when exiting,
    # so the 'finally: await session.close()' is redundant and removed.