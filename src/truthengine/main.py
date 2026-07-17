"""FastAPI application factory for TruthEngine."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from truthengine.api.router import api_router
from truthengine.core.config import Settings, get_settings
from truthengine.core.database import create_database_engine, create_session_factory
from truthengine.core.di import AppContainer
from truthengine.core.exception_handlers import register_exception_handlers
from truthengine.core.logging import configure_logging
from truthengine.core.middleware import register_middlewares
from truthengine.llm.provider import LLMProvider
from truthengine.search.searxng import SearXNGProvider

logger = logging.getLogger(__name__)


def _build_llm_provider(settings: Settings) -> LLMProvider | None:
    """Construct the LLM provider if an API key is configured."""
    if not settings.deepseek_api_key:
        logger.warning(
            "TRUTHENGINE_DEEPSEEK_API_KEY is not set. "
            "LLM pipeline stages will be skipped — investigation will still "
            "collect sources and select passages, but no claim extraction or "
            "verdict will be generated."
        )
        return None
    from truthengine.llm.deepseek import DeepSeekProvider

    return DeepSeekProvider(
        api_key=settings.deepseek_api_key,
        model=settings.deepseek_model,
        base_url=settings.deepseek_base_url,
    )


def create_application(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app_settings = settings or get_settings()
    configure_logging(app_settings)

    engine = create_database_engine(app_settings)
    search_provider = SearXNGProvider(app_settings.searxng_url)
    llm_provider = _build_llm_provider(app_settings)

    container = AppContainer(
        settings=app_settings,
        engine=engine,
        session_factory=create_session_factory(engine),
        search_provider=search_provider,
        llm_provider=llm_provider,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Dispose process-level resources when the application shuts down."""
        yield
        app.state.container.engine.dispose()

    app = FastAPI(
        title="TruthEngine API",
        version=app_settings.app_version,
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.container = container

    # CORS — must be added before other middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_middlewares(app, app_settings)
    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_application()
