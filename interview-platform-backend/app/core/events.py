# app/core/events.py
import logging
from typing import Callable
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def create_start_app_handler(app: FastAPI) -> Callable:
    """
    Returns a function that executes on application startup.
    """
    async def start_app() -> None:
        logger.info("--- Application Startup ---")
        # Example: Initialize database connections, load ML models, etc.
        # try:
        #     await connect_to_database()
        #     logger.info("Database connection established.")
        # except Exception as e:
        #     logger.error(f"Failed to connect to database: {e}")

        # try:
        #     await load_machine_learning_models()
        #     logger.info("Machine learning models loaded.")
        # except Exception as e:
        #     logger.error(f"Failed to load ML models: {e}")
        logger.info("Application startup tasks completed.")

    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:
    """
    Returns a function that executes on application shutdown.
    """
    async def stop_app() -> None:
        logger.info("--- Application Shutdown ---")
        # Example: Close database connections, release resources, etc.
        # try:
        #     await close_database_connection()
        #     logger.info("Database connection closed.")
        # except Exception as e:
        #     logger.error(f"Failed to close database connection: {e}")
        logger.info("Application shutdown tasks completed.")

    return stop_app

# Usage in main.py:
# from app.core.events import create_start_app_handler, create_stop_app_handler
#
# app = FastAPI(...)
# app.add_event_handler("startup", create_start_app_handler(app))
# app.add_event_handler("shutdown", create_stop_app_handler(app))
