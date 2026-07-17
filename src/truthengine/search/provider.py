"""Abstract search provider interface."""

from abc import ABC, abstractmethod

from truthengine.search.models import SearchResult


class SearchProvider(ABC):
    """Abstract boundary for web search integrations."""

    @abstractmethod
    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        """Execute a web search and return ranked results."""
