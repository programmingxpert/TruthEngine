"""DeepSeek LLM provider using the OpenAI-compatible chat completions API."""

import json
import logging
from typing import Any

import httpx

from truthengine.llm.provider import LLMProvider

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0  # LLM calls can be slow


class DeepSeekProvider(LLMProvider):
    """Sends chat completion requests to the DeepSeek API.

    DeepSeek exposes an OpenAI-compatible REST API, so we make raw httpx
    calls rather than importing the openai SDK to keep the dependency tree lean.
    """

    def __init__(self, *, api_key: str, model: str, base_url: str) -> None:
        """Initialize with API credentials and model selection."""
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def complete(self, *, system: str, user: str) -> str:
        """Send a chat completion and return the raw assistant message text."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "temperature": 0.1,
        }
        response = self._post(payload)
        return str(response["choices"][0]["message"]["content"])

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        """Send a chat completion expecting a JSON object and parse the response."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        response = self._post(payload)
        raw_content = str(response["choices"][0]["message"]["content"])
        try:
            parsed: dict[str, Any] = json.loads(raw_content)
            return parsed
        except json.JSONDecodeError as exc:
            logger.error("DeepSeek returned invalid JSON: %s | raw=%r", exc, raw_content[:500])
            return {}

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a POST to the chat completions endpoint and return parsed JSON."""
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                response = client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
        except httpx.HTTPStatusError as exc:
            logger.error(
                "DeepSeek API HTTP error %s: %s",
                exc.response.status_code,
                exc.response.text[:500],
            )
            raise
        except httpx.RequestError as exc:
            logger.error("DeepSeek API connection error: %s", exc)
            raise
