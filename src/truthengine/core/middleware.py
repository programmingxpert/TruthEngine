"""HTTP middleware registration and implementations."""

from collections.abc import Awaitable, Callable
from typing import Final
from uuid import uuid4

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from truthengine.core.config import Settings
from truthengine.core.request_context import reset_request_id, set_request_id

CallNext = Callable[[Request], Awaitable[Response]]

_SECURITY_HEADERS: Final[dict[str, str]] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a stable request ID to every request and response."""

    def __init__(self, app: ASGIApp, *, header_name: str) -> None:
        """Initialize the middleware with the configured request ID header."""
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        """Set request ID context before passing control to the next handler."""
        incoming_request_id = request.headers.get(self.header_name)
        request_id = incoming_request_id.strip() if incoming_request_id else str(uuid4())
        request.state.request_id = request_id
        token = set_request_id(request_id)

        try:
            response = await call_next(request)
            response.headers[self.header_name] = request_id
            return response
        finally:
            reset_request_id(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add conservative security headers to every HTTP response."""

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        """Add security headers after downstream request handling completes."""
        response = await call_next(request)
        for header_name, header_value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header_name, header_value)
        return response


def register_middlewares(app: FastAPI, settings: Settings) -> None:
    """Register HTTP middleware on the application."""
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware, header_name=settings.request_id_header)
