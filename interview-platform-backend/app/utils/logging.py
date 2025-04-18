# app/utils/logging.py
import logging
import sys
from logging.handlers import RotatingFileHandler

# Recommended: Get log level from environment/config
LOG_LEVEL = logging.INFO # Or get from settings: settings.LOG_LEVEL
LOG_FILE = "interview_platform.log"

def setup_logging():
    """
    Configures logging for the application.

    Sets up console and rotating file handlers.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Create a formatter
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(threadName)s - %(message)s"
    )

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    # Avoid adding duplicate handlers if already configured (e.g., by basicConfig)
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
         root_logger.addHandler(console_handler)

    # --- Rotating File Handler ---
    # Creates a log file that rotates when it reaches a certain size.
    # Keeps a specified number of backup files.
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024, # 10 MB
            backupCount=5 # Keep 5 backup logs
        )
        file_handler.setFormatter(log_formatter)
        if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.addHandler(file_handler)
    except Exception as e:
        root_logger.error(f"Failed to set up file logging handler: {e}")


    # --- Configure specific loggers ---
    # Example: Set different levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root_logger.info("Logging configured successfully.")

# --- How to use in main.py ---
# from app.utils.logging import setup_logging
#
# # Call this early, before creating the FastAPI app instance
# setup_logging()
#
# # Then proceed with FastAPI app creation...
# app = FastAPI(...)

# Note: This provides more control than basicConfig.
# If you call setup_logging(), you might remove the basicConfig call from main.py
# to avoid potential conflicts or duplicate handlers, unless you specifically want both.
