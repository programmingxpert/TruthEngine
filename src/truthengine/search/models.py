"""Domain model for web search results."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A single result returned by a web search provider."""

    url: str
    title: str
    snippet: str
