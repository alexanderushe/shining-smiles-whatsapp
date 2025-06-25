# src/utils/logger.py
import logging
import os
from config import get_config

def setup_logger(name):
    """Set up logger with file and console output."""
    config = get_config()
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # File handler
    if not os.path.exists("logs"):
        os.makedirs("logs")
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    # Add handlers
    if not logger.handlers:  # Prevent duplicate handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger