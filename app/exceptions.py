"""Custom exceptions and error handlers."""
from typing import Any, Dict, Optional, List
from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class ApplicationException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class RedisConnectionError(ApplicationException):
    """Redis connection error."""

    def __init__(self, message: str = "Redis connection unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": "redis"}
        )


class TaskNotFoundError(ApplicationException):
    """Task not found error."""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task not found or expired",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": task_id}
        )


class TaskNotCompleteError(ApplicationException):
    """Task not complete error."""

    def __init__(self, task_id: str, current_state: str):
        super().__init__(
            message=f"Task is not complete yet. Current state: {current_state}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"task_id": task_id, "state": current_state}
        )


class InvalidFileError(ApplicationException):
    """Invalid file error."""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Invalid file: {filename}. {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"filename": filename, "reason": reason}
        )


class ProcessingError(ApplicationException):
    """Processing error."""

    def __init__(self, message: str, task_id: Optional[str] = None):
        details = {"task_id": task_id} if task_id else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


async def application_exception_handler(
    request: Request,
    exc: ApplicationException
) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(
        f"Application error: {exc.message} - "
        f"Status: {exc.status_code} - "
        f"Details: {exc.details}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details
            },
            "success": False
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with detailed messages."""
    errors = []

    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        error_type = error["type"]
        message = error["msg"]

        # Create user-friendly error messages
        if error_type == "missing":
            user_message = f"Required field '{field}' is missing"
        elif error_type == "type_error":
            user_message = f"Field '{field}' has invalid type: {message}"
        elif error_type == "value_error":
            user_message = f"Invalid value for field '{field}': {message}"
        else:
            user_message = f"Validation error in '{field}': {message}"

        errors.append({
            "field": field,
            "message": user_message,
            "type": error_type
        })

    logger.warning(
        f"Validation error for {request.method} {request.url.path}: "
        f"{len(errors)} error(s)"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Request validation failed",
                "type": "ValidationError",
                "details": {
                    "errors": errors,
                    "total_errors": len(errors)
                }
            },
            "success": False
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.exception(
        f"Unhandled exception for {request.method} {request.url.path}: "
        f"{str(exc)}"
    )

    # Don't expose internal error details in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "An internal server error occurred. Please try again later.",
                "type": "InternalServerError",
                "details": {
                    "request_id": id(request)
                }
            },
            "success": False
        }
    )


async def http_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle HTTP exceptions with consistent format."""
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": "HTTPException",
                    "details": {
                        "status_code": exc.status_code
                    }
                },
                "success": False
            }
        )

    # Fallback for other exceptions
    return await general_exception_handler(request, exc)
