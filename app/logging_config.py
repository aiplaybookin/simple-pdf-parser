"""Logging configuration."""
import logging
import sys
from datetime import datetime


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f"logs/app_{datetime.now().strftime('%Y%m%d')}.log",
                encoding="utf-8"
            )
        ]
    )

    # Set specific log levels for libraries
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("redis").setLevel(logging.WARNING)  # Reduce Redis noise


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
