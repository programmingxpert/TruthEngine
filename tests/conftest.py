"""Shared pytest fixtures for backend tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from truthengine.core.config import Settings
from truthengine.core.database import Base
from truthengine.main import create_application


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Return a test client with deterministic test settings and an in-memory SQLite database."""
    settings = Settings(environment="test", log_json=False, database_url="sqlite://")
    app = create_application(settings)
    engine = app.state.container.engine
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
