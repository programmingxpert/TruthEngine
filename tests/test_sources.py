"""Tests for the Source Ingestion and Snapshotting bounded context."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from truthengine.sources.domain import SourceCategory
from truthengine.sources.persistence import (
    SqlAlchemySourceRepository,
    SqlAlchemySourceSnapshotRepository,
)
from truthengine.sources.security import normalize_url, validate_dns_ip


def test_url_normalization() -> None:
    """Verify URL components are lowercase, defaults stripped, and query preserved."""
    assert normalize_url("HTTP://Google.com:80/") == "http://google.com/"
    assert normalize_url("https://example.com/path/") == "https://example.com/path"
    assert (
        normalize_url("https://example.com/query?a=1&b=2#frag")
        == "https://example.com/query?a=1&b=2"
    )


@patch("socket.getaddrinfo")
def test_ssrf_validation(mock_getaddrinfo: MagicMock) -> None:
    """Verify DNS resolution blocks loopback, private, and local subnets."""
    # Loopback
    mock_getaddrinfo.return_value = [(2, 1, 6, "", ("127.0.0.1", 0))]
    with pytest.raises(ValueError, match="loopback"):
        validate_dns_ip("localhost")

    # Private IPv4
    mock_getaddrinfo.return_value = [(2, 1, 6, "", ("192.168.1.100", 0))]
    with pytest.raises(ValueError, match="private"):
        validate_dns_ip("my-internal-host")

    # Link-local IPv4
    mock_getaddrinfo.return_value = [(2, 1, 6, "", ("169.254.169.254", 0))]
    with pytest.raises(ValueError, match="link-local"):
        validate_dns_ip("aws-metadata")

    # Public IPv4 (allowed)
    mock_getaddrinfo.return_value = [(2, 1, 6, "", ("8.8.8.8", 0))]
    resolved = validate_dns_ip("dns.google")
    assert resolved == "8.8.8.8"


def test_repository_save_and_retrieve(client: TestClient) -> None:
    """Verify that repositories correctly persist and fetch sources and snapshots."""
    from truthengine.core.di import AppContainer
    from truthengine.sources.domain import Source, SourceSnapshot

    app = cast_app(client)
    container: AppContainer = app.state.container

    with container.session_factory() as session:
        source_repo = SqlAlchemySourceRepository(session)
        snapshot_repo = SqlAlchemySourceSnapshotRepository(session)

        # 1. Add Source
        source = Source(
            id=uuid4(),
            domain="example.org",
            source_category=SourceCategory.GENERAL,
            created_at=datetime.now(UTC),
        )
        source_repo.add(source)
        session.commit()

        # 2. Query Source
        retrieved_source = source_repo.get_by_domain("example.org")
        assert retrieved_source is not None
        assert retrieved_source.id == source.id

        # 3. Add Snapshot
        snapshot = SourceSnapshot(
            id=uuid4(),
            source_id=source.id,
            url="https://example.org/news",
            fetched_at=datetime.now(UTC),
            content_hash="fingerprint123",
            content_type="text/html",
            http_status=200,
            title="News Page",
            extracted_text="Article text content goes here.",
            original_html=(
                "<html><title>News Page</title><body>Article text content goes here.</body></html>"
            ),
            content_length=200,
            fetch_duration_ms=80,
            etag="etag-v1",
            last_modified=datetime.now(UTC),
            encoding="utf-8",
            metadata={"ua": "TruthEngineBot"},
            snapshot_version=1,
        )
        snapshot_repo.add(snapshot)
        session.commit()

        # 4. Query Snapshot
        retrieved_snap = snapshot_repo.get_by_hash(source.id, "fingerprint123")
        assert retrieved_snap is not None
        assert retrieved_snap.title == "News Page"
        assert retrieved_snap.snapshot_version == 1

        # 5. Check version tracking
        assert snapshot_repo.get_latest_version(source.id) == 1


@patch("httpx.Client.stream")
@patch("socket.getaddrinfo")
def test_crawler_deduplication(
    mock_getaddrinfo: MagicMock, mock_stream: MagicMock, client: TestClient
) -> None:
    """Verify that crawling identical text returns the existing snapshot without version bump."""
    # Mock safe DNS IP
    mock_getaddrinfo.return_value = [(2, 1, 6, "", ("8.8.8.8", 0))]

    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html", "content-length": "100"}
    mock_response.encoding = "utf-8"
    mock_response.iter_bytes.return_value = [
        b"<html><title>Page Title</title><body>Clean article text.</body></html>"
    ]
    mock_stream.return_value.__enter__.return_value = mock_response

    # Ingest first time
    resp1 = client.post("/sources/ingest", json={"url": "https://example.com/article"})
    assert resp1.status_code == 201
    snap1 = resp1.json()
    assert snap1["snapshot_version"] == 1
    assert snap1["title"] == "Page Title"

    # Ingest second time with identical content
    resp2 = client.post("/sources/ingest", json={"url": "https://example.com/article"})
    assert resp2.status_code == 201
    snap2 = resp2.json()
    # It must return the exact same snapshot record
    assert snap2["snapshot_id"] == snap1["snapshot_id"]
    assert snap2["snapshot_version"] == 1


@patch("httpx.Client.stream")
@patch("socket.getaddrinfo")
def test_failed_fetch_recording(
    mock_getaddrinfo: MagicMock, mock_stream: MagicMock, client: TestClient
) -> None:
    """Verify that network exceptions map to failed snapshots storing error details."""
    mock_getaddrinfo.return_value = [(2, 1, 6, "", ("8.8.8.8", 0))]

    from httpx import ConnectTimeout

    mock_stream.side_effect = ConnectTimeout("Connection timeout error")

    resp = client.post("/sources/ingest", json={"url": "https://slow-site.org/"})
    assert resp.status_code == 201
    snap = resp.json()

    assert snap["http_status"] is None
    assert snap["title"] == "Failed Fetch"
    assert snap["metadata"]["error_type"] == "timeout"
    assert "timeout" in snap["metadata"]["error_message"]


def cast_app(client: TestClient) -> Any:
    """Return the cast FastAPI application from TestClient."""
    return client.app
