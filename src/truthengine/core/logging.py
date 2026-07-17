"""Structured logging setup for the backend process."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from truthengine.core.config import Settings
from truthengine.core.request_context import get_request_id


class JsonFormatter(logging.Formatter):
    """Format log records as compact JSON objects."""

    def __init__(self, *, service_name: str, environment: str) -> None:
        """Initialize the formatter with stable service metadata."""
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """Render a log record as a JSON string."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
            "request_id": get_request_id(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Preserve simple structured fields passed through logging extra.
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in _STANDARD_LOG_RECORD_FIELDS:
                continue
            if isinstance(value, str | int | float | bool | type(None)):
                payload[key] = value

        return json.dumps(payload, separators=(",", ":"), default=str)


class PlainTextFormatter(logging.Formatter):
    """Format log records as plain text, safely injecting the request ID."""

    def __init__(self) -> None:
        """Initialize the formatter with a static log format."""
        super().__init__(
            "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s",
        )

    def format(self, record: logging.LogRecord) -> str:
        """Render a log record as a plain text string, injecting the request ID."""
        record.request_id = get_request_id() or "-"
        return super().format(record)


def configure_logging(settings: Settings) -> None:
    """Configure process logging according to application settings."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(
            JsonFormatter(service_name=settings.service_name, environment=settings.environment),
        )
    else:
        handler.setFormatter(PlainTextFormatter())

    root_logger.addHandler(handler)

    # Keep server logs flowing through the same formatter so request IDs and
    # deployment metadata are consistent across application and ASGI logs.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        named_logger = logging.getLogger(logger_name)
        named_logger.handlers.clear()
        named_logger.propagate = True


_STANDARD_LOG_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}
