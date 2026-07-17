"""Response schema for the health endpoint."""

from typing import Literal

from pydantic import BaseModel

from truthengine.core.config import Environment


class HealthResponse(BaseModel):
    """Health endpoint response body."""

    status: Literal["ok"]
    service: str
    environment: Environment
    version: str
