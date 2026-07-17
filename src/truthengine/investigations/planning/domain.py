"""Domain interfaces and models for the investigation planner."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class InvestigationPlan:
    """An immutable, deterministic execution plan for an investigation."""

    investigation_id: UUID
    detected_domain: str
    objective: str
    assumptions: list[str]
    required_evidence_categories: list[str]
    preferred_source_categories: list[str]
    excluded_source_categories: list[str]
    retrieval_strategy: str
    success_criteria: list[str]
    limitations: list[str]
    planning_timestamp: datetime
    planner_version: str


class DomainProfile(ABC):
    """Abstract base class for all planning domains."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the domain (e.g. 'Education', 'Technology')."""

    @abstractmethod
    def matches(self, query: str) -> bool:
        """Determine if a query belongs to this domain using deterministic rules."""

    @property
    @abstractmethod
    def preferred_source_categories(self) -> list[str]:
        """Preferred source categories for this domain."""

    @property
    @abstractmethod
    def excluded_source_categories(self) -> list[str]:
        """Excluded source categories for this domain."""

    @property
    @abstractmethod
    def success_criteria_templates(self) -> list[str]:
        """Templates of success criteria for this domain."""

    @abstractmethod
    def generate_plan_details(self, query: str) -> dict[str, Any]:
        """Generate specific planning details for a query."""
