"""Top-level API router for the application."""

from fastapi import APIRouter

from truthengine.api.health import router as health_router
from truthengine.investigations.router import (
    graphs_router,
)
from truthengine.investigations.router import (
    router as investigations_router,
)
from truthengine.sources.router import (
    snapshots_router,
    sources_router,
)

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(investigations_router)
api_router.include_router(graphs_router)
api_router.include_router(sources_router)
api_router.include_router(snapshots_router)
