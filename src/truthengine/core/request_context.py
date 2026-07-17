"""Request-scoped context helpers."""

from contextvars import ContextVar, Token

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Return the request ID bound to the current context, if any."""
    return _request_id.get()


def set_request_id(request_id: str) -> Token[str | None]:
    """Bind a request ID to the current context and return a reset token."""
    return _request_id.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    """Reset the request ID context using a token returned by set_request_id."""
    _request_id.reset(token)
