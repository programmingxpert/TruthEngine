"""Integration tests for investigation endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_investigation_success(client: TestClient) -> None:
    """Creating an investigation with a valid query should return 201 and metadata."""
    response = client.post("/investigations", json={"query": "Is Rust replacing C++?"})

    assert response.status_code == 201
    data = response.json()
    assert "investigation_id" in data
    assert data["status"] == "CREATED"


def test_create_investigation_invalid_query(client: TestClient) -> None:
    """Creating an investigation with an empty query should return 422 validation error."""
    response = client.post("/investigations", json={"query": "   "})
    assert response.status_code == 422


def test_get_investigation_success(client: TestClient) -> None:
    """Retrieving a created investigation should return 200 and details."""
    # First, create it
    create_response = client.post("/investigations", json={"query": "Is Rust replacing C++?"})
    assert create_response.status_code == 201
    inv_id = create_response.json()["investigation_id"]

    # Now, get it
    get_response = client.get(f"/investigations/{inv_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["investigation_id"] == inv_id
    assert data["query"] == "Is Rust replacing C++?"
    assert data["status"] == "CREATED"
    assert "created_at" in data
    assert "updated_at" in data


def test_get_investigation_not_found(client: TestClient) -> None:
    """Retrieving a non-existent investigation should return 404."""
    random_uuid = str(uuid4())
    response = client.get(f"/investigations/{random_uuid}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "investigation_not_found"


def test_service_update_investigation_status(client: TestClient) -> None:
    """Updating investigation status via the service should persist the new status."""
    from typing import cast

    from fastapi import FastAPI

    from truthengine.core.di import AppContainer
    from truthengine.investigations.candidates.persistence import (
        SqlAlchemyCandidatePassageRepository,
        SqlAlchemyDocumentSegmentRepository,
    )
    from truthengine.investigations.domain import InvestigationStatus
    from truthengine.investigations.graphs.persistence import (
        SqlAlchemyEvidenceGraphRepository,
    )
    from truthengine.investigations.persistence import (
        SqlAlchemyInvestigationRepository,
        SqlAlchemyTimelineEventRepository,
    )
    from truthengine.investigations.planning.persistence import (
        SqlAlchemyInvestigationPlanRepository,
    )
    from truthengine.investigations.service import InvestigationService
    from truthengine.sources.persistence import (
        SqlAlchemySourceSnapshotRepository,
    )

    app = cast(FastAPI, client.app)
    container: AppContainer = app.state.container

    with container.session_factory() as session:
        repo = SqlAlchemyInvestigationRepository(session)
        timeline_repo = SqlAlchemyTimelineEventRepository(session)
        plan_repo = SqlAlchemyInvestigationPlanRepository(session)
        graph_repo = SqlAlchemyEvidenceGraphRepository(session)
        snapshot_repo = SqlAlchemySourceSnapshotRepository(session)
        segment_repo = SqlAlchemyDocumentSegmentRepository(session)
        passage_repo = SqlAlchemyCandidatePassageRepository(session)
        service = InvestigationService(
            repo,
            timeline_repo,
            plan_repo,
            graph_repo,
            snapshot_repo,
            segment_repo,
            passage_repo,
        )

        # Create
        investigation = service.create(query="Is Rust replacing C++?")
        inv_id = investigation.id
        assert investigation.status == InvestigationStatus.CREATED

        # Update
        updated = service.update_status(investigation_id=inv_id, status=InvestigationStatus.RUNNING)
        assert updated.status == InvestigationStatus.RUNNING
        session.commit()

    # Read in a new session to verify persistence
    with container.session_factory() as session:
        repo = SqlAlchemyInvestigationRepository(session)
        timeline_repo = SqlAlchemyTimelineEventRepository(session)
        plan_repo = SqlAlchemyInvestigationPlanRepository(session)
        graph_repo = SqlAlchemyEvidenceGraphRepository(session)
        snapshot_repo = SqlAlchemySourceSnapshotRepository(session)
        segment_repo = SqlAlchemyDocumentSegmentRepository(session)
        passage_repo = SqlAlchemyCandidatePassageRepository(session)
        service = InvestigationService(
            repo,
            timeline_repo,
            plan_repo,
            graph_repo,
            snapshot_repo,
            segment_repo,
            passage_repo,
        )
        retrieved = service.get(investigation_id=inv_id)
        assert retrieved.status == InvestigationStatus.RUNNING
        assert retrieved.updated_at > retrieved.created_at


def test_workflow_full_success(client: TestClient) -> None:
    """Running the workflow should transition through all statuses and record timeline events."""
    # 1. Create an investigation
    response = client.post("/investigations", json={"query": "Is Rust replacing C++?"})
    assert response.status_code == 201
    inv_id = response.json()["investigation_id"]

    # 2. Run the workflow
    run_response = client.post(f"/investigations/{inv_id}/run")
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "QUEUED"

    get_response = client.get(f"/investigations/{inv_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "COMPLETED"

    # 3. Get timeline
    timeline_response = client.get(f"/investigations/{inv_id}/timeline")
    assert timeline_response.status_code == 200
    events = timeline_response.json()

    # Verify stages in timeline
    event_types = [e["event_type"] for e in events]
    assert "WORKFLOW_STARTED" in event_types
    assert "STATUS_CHANGED" in event_types
    assert "WORKFLOW_COMPLETED" in event_types

    # Verify message timeline sequence (order)
    statuses = [
        e["metadata"].get("new_status") for e in events if e["event_type"] == "STATUS_CHANGED"
    ]
    assert statuses == ["COLLECTING_SOURCES", "ANALYZING", "GENERATING_REPORT", "COMPLETED"]


def test_workflow_restartability(client: TestClient) -> None:
    """Workflow should checkpoint on failure and resume from the last successful stage."""
    from typing import Any

    # 1. Create an investigation
    response = client.post("/investigations", json={"query": "Is Rust replacing C++?"})
    assert response.status_code == 201
    inv_id = response.json()["investigation_id"]

    # 2. Mock a failure in the ANALYZING stage.
    from truthengine.investigations.workflow import InvestigationWorkflowOrchestrator

    original_analyze = InvestigationWorkflowOrchestrator._analyze

    def failing_analyze(self: Any, investigation: Any) -> None:
        raise ValueError("Simulated Analysis Failure")

    InvestigationWorkflowOrchestrator._analyze = failing_analyze  # type: ignore[method-assign]

    try:
        # Run it. The endpoint queues work; failure is recorded in investigation state.
        run_response = client.post(f"/investigations/{inv_id}/run")
        assert run_response.status_code == 200
        assert run_response.json()["status"] == "QUEUED"

        # Verify status is FAILED in db
        get_response = client.get(f"/investigations/{inv_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "FAILED"

        # Verify timeline events recorded up to FAILED
        timeline_response = client.get(f"/investigations/{inv_id}/timeline")
        assert timeline_response.status_code == 200
        events = timeline_response.json()
        assert len(events) > 0
        assert events[-1]["event_type"] == "WORKFLOW_FAILED"
        assert events[-1]["metadata"]["stage"] == "ANALYZING"

    finally:
        # Restore original mock method
        InvestigationWorkflowOrchestrator._analyze = original_analyze  # type: ignore[method-assign]

    # 3. Resume the workflow (should succeed now)
    resume_response = client.post(f"/investigations/{inv_id}/run")
    assert resume_response.status_code == 200
    assert resume_response.json()["status"] == "QUEUED"

    # Verify status is COMPLETED in db
    get_response2 = client.get(f"/investigations/{inv_id}")
    assert get_response2.json()["status"] == "COMPLETED"

    # Verify timeline events show completed
    timeline_response2 = client.get(f"/investigations/{inv_id}/timeline")
    events2 = timeline_response2.json()
    assert events2[-1]["event_type"] == "WORKFLOW_COMPLETED"


def test_delete_investigation_success(client: TestClient) -> None:
    """Deleting a created investigation should return 204 and remove it from database."""
    # Create it
    create_response = client.post("/investigations", json={"query": "Is Rust replacing C++?"})
    assert create_response.status_code == 201
    inv_id = create_response.json()["investigation_id"]

    # Delete it
    delete_response = client.delete(f"/investigations/{inv_id}")
    assert delete_response.status_code == 204

    # Try to retrieve it, should be 404
    get_response = client.get(f"/investigations/{inv_id}")
    assert get_response.status_code == 404


def test_delete_investigation_not_found(client: TestClient) -> None:
    """Deleting a non-existent investigation should return 404."""
    random_uuid = str(uuid4())
    response = client.delete(f"/investigations/{random_uuid}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "investigation_not_found"
