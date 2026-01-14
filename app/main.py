"""Main application entry point."""
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from app.config import settings
from app.routes import api
from app.logging_config import setup_logging, get_logger
from app.middleware import LoggingMiddleware, ErrorLoggingMiddleware
from app.exceptions import (
    ApplicationException,
    application_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    http_exception_handler
)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Setup logging
setup_logging()
logger = get_logger(__name__)

redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan."""
    global redis_client

    # Startup
    logger.info("Starting up...")
    redis_client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    # Set redis client in routes
    api.set_redis_client(redis_client)
    logger.info("Redis connected")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if redis_client:
        await redis_client.close()
    logger.info("Redis disconnected")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    logger.info("Creating FastAPI application...")

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        lifespan=lifespan
    )

    # Register exception handlers
    logger.info("Registering exception handlers...")
    app.add_exception_handler(ApplicationException, application_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server and common React ports
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add middleware (order matters - first added is outermost)
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Include routers
    app.include_router(api.router)

    logger.info("FastAPI application created successfully")
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
