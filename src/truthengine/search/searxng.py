"""SearXNG search provider implementation with DuckDuckGo HTML fallback."""

import logging
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from truthengine.search.models import SearchResult
from truthengine.search.provider import SearchProvider

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0
_USER_AGENT = "TruthEngineBot/1.0.0 (+https://truthengine.org/bot)"


class SearXNGProvider(SearchProvider):
    """Queries a self-hosted SearXNG instance with a robust DuckDuckGo HTML fallback."""

    def __init__(self, base_url: str) -> None:
        """Initialize with the SearXNG base URL."""
        self._base_url = base_url.rstrip("/")

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        """Execute search, falling back to DuckDuckGo HTML scraping if SearXNG fails or returns 0 results."""
        results: list[SearchResult] = []
        seen_urls: set[str] = set()

        # 1. Attempt SearXNG search
        try:
            logger.info("Querying SearXNG search: %s", self._base_url)
            with httpx.Client(timeout=_TIMEOUT) as client:
                response = client.get(
                    f"{self._base_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "categories": "general",
                        "language": "en",
                    },
                    headers={"User-Agent": _USER_AGENT},
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("results", []):
                    url = item.get("url", "").strip()
                    if not url or url in seen_urls:
                        continue
                    if not url.startswith(("http://", "https://")):
                        continue

                    seen_urls.add(url)
                    results.append(
                        SearchResult(
                            url=url,
                            title=item.get("title", "").strip() or url,
                            snippet=item.get("content", "").strip(),
                        )
                    )
                    if len(results) >= max_results:
                        break

                logger.info("SearXNG query completed. Found %d results.", len(results))

        except Exception as exc:
            logger.warning("SearXNG search request failed: %s. Proceeding to DuckDuckGo fallback.", exc)

        # 2. Trigger DuckDuckGo HTML fallback if no results were found
        if not results:
            logger.info("Activating fallback DuckDuckGo HTML search for query: %r", query)
            try:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                }
                with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
                    response = client.get(
                        "https://html.duckduckgo.com/html/",
                        params={"q": query},
                        headers=headers,
                    )
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")

                    for a_tag in soup.find_all("a", class_="result__url"):
                        url = a_tag.get("href", "").strip()
                        if not url:
                            continue

                        # Resolve redirect wrapper URLs if present
                        if "duckduckgo.com/l/?kh=" in url:
                            parsed_url = urlparse(url)
                            qd = parse_qs(parsed_url.query)
                            if "uddg" in qd:
                                url = qd["uddg"][0]

                        if not url.startswith(("http://", "https://")) or url in seen_urls:
                            continue

                        # Extract metadata
                        parent = a_tag.find_parent("div", class_="result__body")
                        title = ""
                        snippet = ""
                        if parent:
                            title_a = parent.find("a", class_="result__snippet") or parent.find("a", class_="result__title")
                            if title_a:
                                title = title_a.get_text(strip=True)
                            snippet_div = parent.find("a", class_="result__snippet")
                            if snippet_div:
                                snippet = snippet_div.get_text(strip=True)

                        if not title:
                            title = a_tag.get_text(strip=True) or url

                        seen_urls.add(url)
                        results.append(
                            SearchResult(
                                url=url,
                                title=title,
                                snippet=snippet,
                            )
                        )
                        if len(results) >= max_results:
                            break

                logger.info("DuckDuckGo HTML fallback search complete. Found %d results.", len(results))

            except Exception as ddg_exc:
                logger.warning("DuckDuckGo fallback search failed: %s", ddg_exc)

        return results
