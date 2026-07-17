"""Tests for candidate passage segmentation and selection."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from truthengine.core.di import AppContainer
from truthengine.investigations.candidates.domain import (
    CandidatePassage,
    DocumentSegment,
    SelectionPolicy,
)
from truthengine.investigations.candidates.persistence import (
    SqlAlchemyCandidatePassageRepository,
    SqlAlchemyDocumentSegmentRepository,
)
from truthengine.investigations.candidates.selector import (
    rank_and_select_passages,
    segment_snapshot,
)
from truthengine.investigations.planning.profiles import TechnologyProfile


def test_segmentation_logic() -> None:
    """Verify that raw text is segmented into paragraphs with heading hierarchy."""
    text = (
        "SECTION 1: INTRODUCTION\n"
        "This is the first paragraph under introduction.\n"
        "Here is the second paragraph.\n"
        "SECTION 2: BACKGROUND\n"
        "This is a paragraph under background."
    )
    snapshot_id = uuid4()

    segments = segment_snapshot(snapshot_id, text)

    # 3 paragraphs total should be extracted (headings are skipped as segments)
    assert len(segments) == 3

    # Segment 1 details
    assert segments[0].heading == "SECTION 1: INTRODUCTION"
    assert segments[0].heading_level == 2
    assert segments[0].paragraph_order == 1
    assert segments[0].content == "This is the first paragraph under introduction."

    # Segment 2 details
    assert segments[1].heading == "SECTION 1: INTRODUCTION"
    assert segments[1].paragraph_order == 2

    # Segment 3 details
    assert segments[2].heading == "SECTION 2: BACKGROUND"
    assert segments[2].heading_level == 2
    assert segments[2].paragraph_order == 3
    assert segments[2].content == "This is a paragraph under background."


def test_ranking_and_policy() -> None:
    """Verify ranking scores query and header overlap and applies limits."""
    snapshot_id = uuid4()
    segments = [
        DocumentSegment(
            id=uuid4(),
            snapshot_id=snapshot_id,
            order=1,
            heading="Performance benchmarks",
            heading_level=3,
            paragraph_order=1,
            parent_section="Benchmarks",
            content="Rust executes very fast, beating python performance.",
            character_range_start=0,
            character_range_end=50,
            token_estimate=12,
        ),
        DocumentSegment(
            id=uuid4(),
            snapshot_id=snapshot_id,
            order=2,
            heading="History of compilers",
            heading_level=3,
            paragraph_order=2,
            parent_section="History",
            content="Compiler construction has evolved since the 1950s.",
            character_range_start=55,
            character_range_end=110,
            token_estimate=12,
        ),
    ]

    policy = SelectionPolicy(min_lexical_threshold=1.0, max_returned_passages=1)
    profile = TechnologyProfile()
    investigation_id = uuid4()

    # Query for Rust performance
    passages = rank_and_select_passages(
        investigation_id=investigation_id,
        query="Rust performance",
        segments=segments,
        snapshot_version=1,
        policy=policy,
        profile=profile,
    )

    # Policy limit of 1 should return only the first matching segment
    assert len(passages) == 1
    p = passages[0]
    assert p.paragraph_order == 1
    assert "rust" in p.selection_explanation["matched_query_terms"]
    assert "performance" in p.selection_explanation["matched_query_terms"]
    assert p.selection_explanation["matched_heading"] == "Performance benchmarks"
    # Tech profile matches tech keywords: performance
    assert any(
        "technology_profile_match" in rule
        for rule in p.selection_explanation["matched_domain_rules"]
    )


def test_repositories_persist(client: TestClient) -> None:
    """Verify document segments and selected passages are persisted and loaded correctly."""
    app = cast_app(client)
    container: AppContainer = app.state.container

    # Create dummy investigation and snapshot first (foreign keys)
    from truthengine.investigations.domain import create_investigation
    from truthengine.investigations.persistence import (
        SqlAlchemyInvestigationRepository,
    )
    from truthengine.sources.domain import Source, SourceCategory, SourceSnapshot
    from truthengine.sources.persistence import (
        SqlAlchemySourceRepository,
        SqlAlchemySourceSnapshotRepository,
    )

    with container.session_factory() as session:
        inv_repo = SqlAlchemyInvestigationRepository(session)
        source_repo = SqlAlchemySourceRepository(session)
        snapshot_repo = SqlAlchemySourceSnapshotRepository(session)

        investigation = create_investigation("Is Rust replacing C++?")
        inv_repo.add(investigation)

        source = Source(
            id=uuid4(),
            domain="c-code.com",
            source_category=SourceCategory.NEWS,
            created_at=datetime.now(UTC),
        )
        source_repo.add(source)
        session.commit()

        snapshot = SourceSnapshot(
            id=uuid4(),
            source_id=source.id,
            url="https://c-code.com/performance",
            fetched_at=datetime.now(UTC),
            content_hash="hashabc123",
            content_type="text/html",
            http_status=200,
            title="Performance comparisons",
            extracted_text="Some performance benchmarks.",
            original_html="<html><title>Performance comparisons</title></html>",
            content_length=100,
            fetch_duration_ms=20,
            etag="etag",
            last_modified=None,
            encoding="utf-8",
            metadata={},
            snapshot_version=1,
        )
        snapshot_repo.add(snapshot)
        session.commit()

        # Add segment and passage
        segment_repo = SqlAlchemyDocumentSegmentRepository(session)
        passage_repo = SqlAlchemyCandidatePassageRepository(session)

        segment = DocumentSegment(
            id=uuid4(),
            snapshot_id=snapshot.id,
            order=1,
            heading="Benchmarks",
            heading_level=2,
            paragraph_order=1,
            parent_section="Benchmarks",
            content="Some performance benchmarks.",
            character_range_start=0,
            character_range_end=28,
            token_estimate=7,
        )
        segment_repo.add_all([segment])
        session.commit()

        passage = CandidatePassage(
            id=uuid4(),
            investigation_id=investigation.id,
            segment_id=segment.id,
            snapshot_version=1,
            algorithm_version="1.0.0",
            paragraph_order=1,
            selection_explanation={"lexical_score": 3.5},
            selected_at=datetime.now(UTC),
        )
        passage_repo.add_all([passage])
        session.commit()

        # Fetch back
        fetched_segs = segment_repo.get_by_snapshot_id(snapshot.id)
        assert len(fetched_segs) == 1
        assert fetched_segs[0].content == "Some performance benchmarks."

        fetched_passages = passage_repo.get_by_investigation_id(investigation.id)
        assert len(fetched_passages) == 1
        assert fetched_passages[0].paragraph_order == 1


def test_passage_selection_api_pipeline(client: TestClient) -> None:
    """Integration test validating plan generation, selection, and retrieval via API."""
    # 1. Create an investigation
    resp = client.post(
        "/investigations",
        json={"query": "Explain student learning curves in school."},
    )
    assert resp.status_code == 201
    inv_id = resp.json()["investigation_id"]

    # 2. Generate plan (needed by selector)
    plan_resp = client.post(f"/investigations/{inv_id}/plan")
    assert plan_resp.status_code == 200

    # 3. Fetching candidates should return empty list initially
    get_resp = client.get(f"/investigations/{inv_id}/candidates")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 0

    # 4. Mock crawl/ingest a relevant source
    # We patch socket DNS and response streaming to populate a snapshot in DB
    with (
        patch("socket.getaddrinfo") as mock_dns,
        patch("httpx.Client.stream") as mock_stream,
    ):
        mock_dns.return_value = [(2, 1, 6, "", ("8.8.8.8", 0))]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.encoding = "utf-8"
        mock_response.iter_bytes.return_value = [
            b"<html><title>Education Study</title><body>The student learning "
            b"curve matches standard academic curves.</body></html>"
        ]
        mock_stream.return_value.__enter__.return_value = mock_response

        ingest_resp = client.post("/sources/ingest", json={"url": "https://school.edu/study"})
        assert ingest_resp.status_code == 201

    # 5. POST to run candidate selection
    select_resp = client.post(f"/investigations/{inv_id}/candidates")
    assert select_resp.status_code == 200
    passages = select_resp.json()
    assert len(passages) >= 1
    p = passages[0]

    assert p["investigation_id"] == inv_id
    assert p["paragraph_order"] == 1
    assert p["selection_explanation"]["matched_heading"] == "Education Study"
    assert "student" in p["selection_explanation"]["matched_query_terms"]

    # Education profile matching words like student, academic
    domain_rules = p["selection_explanation"]["matched_domain_rules"]
    assert any("education_profile" in rule for rule in domain_rules)

    # 6. GET candidates should now return the persisted results
    get_resp2 = client.get(f"/investigations/{inv_id}/candidates")
    assert get_resp2.status_code == 200
    assert len(get_resp2.json()) == len(passages)
    assert get_resp2.json()[0]["passage_id"] == p["passage_id"]


def cast_app(client: TestClient) -> Any:
    """Return the cast FastAPI application from TestClient."""
    return client.app
