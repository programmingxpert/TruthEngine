"""Tests for the deterministic planning module."""

from fastapi.testclient import TestClient

from truthengine.investigations.planning.planner import InvestigationPlanner
from truthengine.investigations.planning.profiles import (
    EducationProfile,
    GeneralProfile,
    TechnologyProfile,
)


def test_domain_selection() -> None:
    """Verify queries map to the expected DomainProfile."""
    planner = InvestigationPlanner()

    # Education queries
    assert planner._select_profile("Is Alliance University ranked #1 in India?").name == "Education"
    assert planner._select_profile("What is the placement percentage of IIT?").name == "Education"

    # Tech queries
    assert planner._select_profile("Is Rust replacing C++?").name == "Technology"
    assert planner._select_profile("Explain python benchmarks").name == "Technology"

    # Fallback queries
    assert planner._select_profile("Is the earth flat?").name == "General"
    assert planner._select_profile("Who won the 2024 election?").name == "General"


def test_planning_rules() -> None:
    """Verify that profiles define correct rules and constraints."""
    edu = EducationProfile()
    assert "Reddit" in edu.excluded_source_categories
    assert "Government" in edu.preferred_source_categories
    assert len(edu.success_criteria_templates) > 0

    tech = TechnologyProfile()
    assert "Reddit" in tech.excluded_source_categories
    assert "Official documentation" in tech.preferred_source_categories
    assert len(tech.success_criteria_templates) > 0

    gen = GeneralProfile()
    assert "Forums" in gen.excluded_source_categories
    assert len(gen.success_criteria_templates) > 0


def test_plan_snapshot() -> None:
    """Snapshot validation of generated plan fields to prevent regression."""
    from uuid import uuid4

    planner = InvestigationPlanner()
    plan = planner.plan(
        investigation_id=uuid4(),
        query="Is Alliance University ranked #1 in India?",
    )

    assert plan.detected_domain == "Education"
    assert plan.preferred_source_categories == [
        "Government",
        "Ranking organizations",
        "Official university website",
    ]
    assert plan.excluded_source_categories == [
        "Reddit",
        "Blogs",
        "Marketing pages",
        "AI-generated summaries",
    ]
    assert plan.required_evidence_categories == [
        "Government rankings",
        "Independent rankings",
        "International rankings",
        "Official university claims",
    ]
    assert plan.planner_version == "1.0.0"


def test_plan_integration_api(client: TestClient) -> None:
    """Integration test verifying creation, persistence, and retrieval of plan via REST API."""
    # 1. Create an investigation
    resp = client.post(
        "/investigations", json={"query": "Is Alliance University ranked #1 in India?"}
    )
    assert resp.status_code == 201
    inv_id = resp.json()["investigation_id"]

    # 2. Generate Plan (POST)
    plan_resp = client.post(f"/investigations/{inv_id}/plan")
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()

    assert plan_data["investigation_id"] == inv_id
    assert plan_data["detected_domain"] == "Education"
    assert (
        "At least two independent ranking organizations verified" in plan_data["success_criteria"]
    )
    assert "Government" in plan_data["preferred_source_categories"]

    # 3. Retrieve Plan (GET)
    get_resp = client.get(f"/investigations/{inv_id}/plan")
    assert get_resp.status_code == 200
    assert get_resp.json()["detected_domain"] == "Education"
    assert get_resp.json()["planner_version"] == "1.0.0"
