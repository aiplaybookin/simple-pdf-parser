"""Middleware for logging and monitoring."""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = id(request)

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Log query parameters if present
        if request.url.query:
            logger.debug(f"[{request_id}] Query params: {request.url.query}")

        # Track request time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )

            # Add custom headers
            response.headers["X-Request-ID"] = str(request_id)
            response.headers["X-Process-Time"] = f"{duration:.3f}"

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration:.3f}s",
                exc_info=True
            )
            raise


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and log all exceptions."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Catch and log exceptions."""
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception(
                f"Unhandled exception for {request.method} {request.url.path}: {str(e)}"
            )
            raise
