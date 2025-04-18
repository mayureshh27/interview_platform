# app/tools/init_db.py
import os
import asyncio
from sqlalchemy import text
from dotenv import load_dotenv
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables once at the start
load_dotenv()

# IMPORTANT: Ensure your DATABASE_URL environment variable does NOT contain
# ?sslmode=require or ?ssl=require when using connect_args={'ssl': 'require'}

async def init_neon_db():
    """Initialize and test Neon PostgreSQL connection and perform basic setup."""
    print("Initializing Neon PostgreSQL database...")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found.")
        print("Please ensure your .env file exists and contains DATABASE_URL.")
        return False

    # --- Preferred Approach (Modify Dialect directly) ---
    try:
        print("Attempting connection using direct URL modification...")
        # Replace the standard 'postgresql' dialect with 'postgresql+asyncpg'
        # The ssl requirement is handled via connect_args
        connection_string = database_url.replace('postgresql://', 'postgresql+asyncpg://')

        # Create async engine and verify connection
        engine = create_async_engine(
            connection_string,
            echo=True,
            connect_args={'ssl': 'require'} # <-- Add this
        )

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"Connection successful! PostgreSQL version: {version}")

        await engine.dispose()
        print("Database initialization completed successfully.")
        return True

    except Exception as e:
        print(f"ERROR: Failed to connect/initialize using direct URL modification: {e}")
        print(f"Details: {e}") # Print error details
        print("Trying urlparse alternative connection approach...")

    # --- Alternative Approach (Using urlparse) ---
    try:
        tmpPostgres = urlparse(database_url)
        # Reconstruct URL explicitly including asyncpg dialect
        # The ssl requirement is handled via connect_args
        engine = create_async_engine(
            f"postgresql+asyncpg://{tmpPostgres.username}:{tmpPostgres.password}@{tmpPostgres.hostname}{tmpPostgres.path}", # <-- Removed query parameters here
            echo=True,
            connect_args={'ssl': 'require'} # <-- Add this
        )

        async with engine.connect() as conn:
            result = await conn.execute(text("select 'hello world'"))
            print(f"Alternative connection method successful! Result: {result.fetchall()}")

        await engine.dispose()
        return True

    except Exception as e2:
        print(f"ERROR: Alternative connection also failed: {e2}")
        print(f"Details: {e2}") # Print error details
        return False


# Simple test function matching the original Neon example structure
async def async_main():
    print("Testing connection using Neon's *original example* code structure...")
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("ERROR: DATABASE_URL environment variable not found.")
        return False

    try:
        tmpPostgres = urlparse(db_url)

        # Create async engine - ensure the URL doesn't have ssl params
        engine = create_async_engine(
            f"postgresql+asyncpg://{tmpPostgres.username}:{tmpPostgres.password}@{tmpPostgres.hostname}{tmpPostgres.path}", # <-- Removed query parameters here
            echo=True,
            connect_args={'ssl': 'require'} # <-- Add this
        )
        async with engine.connect() as conn:
            result = await conn.execute(text("select 'hello world'"))
            print(f"Original test successful! Result: {result.fetchall()}")
        await engine.dispose()
        print("Original test function completed.")
        return True
    except Exception as e:
        print(f"ERROR: Original test function failed: {e}")
        print(f"Details: {e}") # Print error details
        return False

if __name__ == "__main__":
    print("Running database initialization test...")
    # This will call init_neon_db, which tries two connection methods
    asyncio.run(init_neon_db())

    # You can optionally uncomment to run the original simple test as well
    # print("\nRunning original simple connection test...")
    # asyncio.run(async_main())