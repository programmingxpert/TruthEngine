"""Health endpoint for operational readiness checks."""

from typing import Annotated

from fastapi import APIRouter, Depends

from truthengine.core.config import Settings
from truthengine.core.di import get_settings_from_container
from truthengine.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health(
    settings: Annotated[Settings, Depends(get_settings_from_container)],
) -> HealthResponse:
    """Return basic service health without touching downstream dependencies."""
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        environment=settings.environment,
        version=settings.app_version,
    )
