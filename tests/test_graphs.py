"""Tests for the versioned evidence graph storage module."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from truthengine.core.di import AppContainer
from truthengine.investigations.graphs.domain import (
    Claim,
    ClaimStatus,
    ClaimType,
    EvidenceGraph,
    EvidenceItem,
    EvidenceRelation,
    RelationType,
)
from truthengine.investigations.graphs.persistence import (
    SqlAlchemyEvidenceGraphRepository,
)


def test_repository_save_and_retrieve(client: TestClient) -> None:
    """Verify that the repository correctly persists and eagerly loads the complete graph."""
    app = cast(FastAPI, client.app)
    container: AppContainer = app.state.container

    with container.session_factory() as session:
        repo = SqlAlchemyEvidenceGraphRepository(session)

        # 1. Create a dummy investigation first (foreign key dependency)
        from truthengine.investigations.domain import create_investigation
        from truthengine.investigations.persistence import (
            SqlAlchemyInvestigationRepository,
        )

        inv_repo = SqlAlchemyInvestigationRepository(session)
        investigation = create_investigation("Test query")
        inv_repo.add(investigation)
        session.commit()

        # 2. Build graph domain objects
        graph_id = uuid4()
        claim_id = uuid4()
        item_id = uuid4()
        rel_id = uuid4()

        claim = Claim(
            id=claim_id,
            graph_id=graph_id,
            text="Rust is faster than Python.",
            claim_type=ClaimType.PRIMARY,
            status=ClaimStatus.UNVERIFIED,
        )
        evidence_item = EvidenceItem(
            id=item_id,
            graph_id=graph_id,
            source_snapshot_id=uuid4(),
            quote="Rust executes benchmarks in 10ms whereas Python takes 200ms.",
            location="Page 10, Table 2",
            extracted_at=datetime.now(UTC),
        )
        relation = EvidenceRelation(
            id=rel_id,
            graph_id=graph_id,
            claim_id=claim_id,
            evidence_item_id=item_id,
            relation_type=RelationType.SUPPORTS,
        )

        graph = EvidenceGraph(
            id=graph_id,
            investigation_id=investigation.id,
            version=1,
            created_at=datetime.now(UTC),
            claims=[claim],
            evidence_items=[evidence_item],
            relations=[relation],
        )

        # 3. Save to repository
        repo.add(graph)
        session.commit()

        # 4. Fetch back and assert
        fetched = repo.get_by_id(graph_id)
        assert fetched is not None
        assert fetched.investigation_id == investigation.id
        assert fetched.version == 1
        assert len(fetched.claims) == 1
        assert fetched.claims[0].text == "Rust is faster than Python."
        assert len(fetched.evidence_items) == 1
        assert "benchmark" in fetched.evidence_items[0].quote
        assert len(fetched.relations) == 1
        assert fetched.relations[0].relation_type == RelationType.SUPPORTS


def test_graph_versioning_and_latest(client: TestClient) -> None:
    """Verify that multiple versions can be saved and get_latest_by_investigation_id works."""
    app = cast(FastAPI, client.app)
    container: AppContainer = app.state.container

    with container.session_factory() as session:
        repo = SqlAlchemyEvidenceGraphRepository(session)

        from truthengine.investigations.domain import create_investigation
        from truthengine.investigations.persistence import (
            SqlAlchemyInvestigationRepository,
        )

        inv_repo = SqlAlchemyInvestigationRepository(session)
        investigation = create_investigation("Test query")
        inv_repo.add(investigation)
        session.commit()

        inv_id = investigation.id

        # Create Version 1 (Empty)
        graph_v1 = EvidenceGraph(
            id=uuid4(),
            investigation_id=inv_id,
            version=1,
            created_at=datetime.now(UTC),
            claims=[],
            evidence_items=[],
            relations=[],
        )
        repo.add(graph_v1)
        session.commit()

        # Create Version 2 (Additive edit)
        graph_v2 = EvidenceGraph(
            id=uuid4(),
            investigation_id=inv_id,
            version=2,
            created_at=datetime.now(UTC),
            claims=[
                Claim(
                    id=uuid4(),
                    graph_id=graph_v1.id,  # Will overwrite below
                    text="Claim in version 2",
                    claim_type=ClaimType.PRIMARY,
                    status=ClaimStatus.UNVERIFIED,
                )
            ],
            evidence_items=[],
            relations=[],
        )
        # Fix the graph_id on the claim in graph_v2
        graph_v2.claims[0] = Claim(
            id=graph_v2.claims[0].id,
            graph_id=graph_v2.id,
            text=graph_v2.claims[0].text,
            claim_type=graph_v2.claims[0].claim_type,
            status=graph_v2.claims[0].status,
        )

        repo.add(graph_v2)
        session.commit()

        # Get latest
        latest = repo.get_latest_by_investigation_id(inv_id)
        assert latest is not None
        assert latest.version == 2
        assert len(latest.claims) == 1
        assert latest.claims[0].text == "Claim in version 2"


def test_graph_api_endpoints(client: TestClient) -> None:
    """Integration test verifying creation, fetching latest, and querying by ID via REST API."""
    # 1. Create an investigation
    resp = client.post("/investigations", json={"query": "Is Rust replacing C++?"})
    assert resp.status_code == 201
    inv_id = resp.json()["investigation_id"]

    # 2. Verify latest graph returns 200 OK (automatically initialized empty v1 graph) before manual creation
    latest_resp = client.get(f"/investigations/{inv_id}/graphs/latest")
    assert latest_resp.status_code == 200
    graph_data = latest_resp.json()
    graph_id = graph_data["graph_id"]
    assert graph_data["investigation_id"] == inv_id
    assert graph_data["version"] == 1
    assert len(graph_data["claims"]) == 0

    # 3. Create Version 1 (POST - should be idempotent and return existing graph_id)
    create_resp = client.post(f"/investigations/{inv_id}/graphs")
    assert create_resp.status_code == 201
    assert create_resp.json()["graph_id"] == graph_id

    # 4. Fetch latest graph again (GET)
    latest_resp2 = client.get(f"/investigations/{inv_id}/graphs/latest")
    assert latest_resp2.status_code == 200
    assert latest_resp2.json()["graph_id"] == graph_id

    # 5. Fetch by ID (GET /graphs/{graph_id})
    by_id_resp = client.get(f"/graphs/{graph_id}")
    assert by_id_resp.status_code == 200
    assert by_id_resp.json()["investigation_id"] == inv_id
    assert by_id_resp.json()["version"] == 1
