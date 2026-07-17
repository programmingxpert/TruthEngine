"""Repository interface for persisting and querying versioned evidence graphs."""

from abc import ABC, abstractmethod
from uuid import UUID

from truthengine.investigations.graphs.domain import EvidenceGraph


class EvidenceGraphRepository(ABC):
    """Persistence boundary for versioned evidence graphs."""

    @abstractmethod
    def add(self, graph: EvidenceGraph) -> None:
        """Persist a new version of the evidence graph with all its nodes and edges."""

    @abstractmethod
    def get_by_id(self, graph_id: UUID) -> EvidenceGraph | None:
        """Return the evidence graph by ID, including all its claims, items, and relations."""

    @abstractmethod
    def get_latest_by_investigation_id(self, investigation_id: UUID) -> EvidenceGraph | None:
        """Return the latest version of the evidence graph, if one exists."""
