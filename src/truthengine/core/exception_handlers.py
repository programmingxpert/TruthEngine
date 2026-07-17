"""Exception handlers that return consistent JSON error responses."""

import logging
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from truthengine.core.request_context import get_request_id

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application exception for expected operational failures."""

    def __init__(self, *, code: str, message: str, status_code: int = 500) -> None:
        """Initialize an application error with a stable code and HTTP status."""
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def build_error_payload(*, code: str, message: str, request: Request) -> dict[str, Any]:
    """Build the public JSON error payload shared by all exception handlers."""
    request_id = get_request_id() or getattr(request.state, "request_id", None)
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        },
    }


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle expected application errors."""
    app_error = cast(AppError, exc)
    payload = build_error_payload(code=app_error.code, message=app_error.message, request=request)
    return JSONResponse(status_code=app_error.status_code, content=payload)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle FastAPI HTTP exceptions with the shared error response shape."""
    http_error = cast(HTTPException, exc)
    message = str(http_error.detail)
    payload = build_error_payload(code="http_error", message=message, request=request)
    return JSONResponse(
        status_code=http_error.status_code,
        content=payload,
        headers=http_error.headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions without leaking internals to callers."""
    logger.exception("Unhandled request error", extra={"path": request.url.path})
    payload = build_error_payload(
        code="internal_server_error",
        message="An unexpected error occurred.",
        request=request,
    )
    return JSONResponse(status_code=500, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers on a FastAPI instance."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
