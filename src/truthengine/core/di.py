"""Dependency injection primitives for the FastAPI application."""

from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from truthengine.core.config import Settings
from truthengine.core.database import session_scope
from truthengine.llm.provider import LLMProvider
from truthengine.search.provider import SearchProvider


@dataclass(frozen=True, slots=True)
class AppContainer:
    """Small dependency container for process-level application dependencies."""

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    search_provider: SearchProvider
    llm_provider: LLMProvider | None


def get_container(request: Request) -> AppContainer:
    """Resolve the application container from FastAPI application state."""
    container = getattr(request.app.state, "container", None)
    if not isinstance(container, AppContainer):
        msg = "Application container is not configured."
        raise RuntimeError(msg)
    return container


def get_settings_from_container(
    container: Annotated[AppContainer, Depends(get_container)],
) -> Settings:
    """Resolve application settings through the dependency container."""
    return container.settings


def get_database_session(
    container: Annotated[AppContainer, Depends(get_container)],
) -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""
    yield from session_scope(container.session_factory)


def get_search_provider(
    container: Annotated[AppContainer, Depends(get_container)],
) -> SearchProvider:
    """Resolve the search provider from the application container."""
    return container.search_provider


def get_llm_provider(
    container: Annotated[AppContainer, Depends(get_container)],
) -> LLMProvider | None:
    """Resolve the optional LLM provider from the application container."""
    return container.llm_provider
