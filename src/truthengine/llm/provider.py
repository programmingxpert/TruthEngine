"""Abstract LLM provider interface for TruthEngine pipeline stages."""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract boundary for LLM integrations used across pipeline stages."""

    @abstractmethod
    def complete(self, *, system: str, user: str) -> str:
        """Send a chat completion request and return the raw text response."""

    @abstractmethod
    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        """Send a chat completion request expecting a JSON object response."""
