"""Tests for the health endpoint and baseline HTTP behavior."""

from fastapi.testclient import TestClient


def test_health_returns_service_status(client: TestClient) -> None:
    """Health endpoint should return the service status payload."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "truthengine-api",
        "environment": "test",
        "version": "0.1.0",
    }


def test_health_returns_request_id_header(client: TestClient) -> None:
    """Health endpoint should echo caller-provided request IDs."""
    response = client.get("/health", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"


def test_openapi_schema_is_exposed_for_frontend_contracts(client: TestClient) -> None:
    """OpenAPI should be exposed now that the frontend depends on API contracts."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
