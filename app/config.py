"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # Redis configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    STREAM_NAME: str = "pdf_processing_tasks"
    CONSUMER_GROUP: str = "pdf_workers"
    CONSUMER_NAME: str = os.getenv("WORKER_NAME", "worker_1")

    # Gemini configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"

    # Processing configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "5000"))  # words per chunk
    TASK_EXPIRATION: int = 3600  # seconds (1 hour)

    # API configuration
    API_TITLE: str = "Intelligent Document Processing API"
    API_VERSION: str = "3.0"
    API_DESCRIPTION: str = "Async document processing with Redis Streams and AI Summarization"


settings = Settings()
