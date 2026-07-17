"""Ingestion pipeline fetching clean textual content and parsing HTML elements."""

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime

import httpx
import trafilatura
from bs4 import BeautifulSoup

USER_AGENT = "TruthEngineBot/1.0.0 (+https://truthengine.org/bot)"
MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5 MB
TIMEOUT = 10.0


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Consolidated parameters representing a successful scrape or specific network fault."""

    url: str
    fetched_at: datetime
    success: bool
    http_status: int | None
    content_type: str
    title: str
    extracted_text: str
    original_html: str
    content_length: int | None
    fetch_duration_ms: int | None
    etag: str | None
    last_modified: datetime | None
    encoding: str | None
    error_type: str | None  # "timeout", "dns", "ssl", "redirect_loop", "blocked_host", etc.
    error_message: str | None


def compute_fingerprint(text: str) -> str:
    """Calculate a deterministic SHA-256 fingerprint of clean parsed text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fetch_url(url: str) -> FetchResult:
    """Stream and validate a target webpage URL, guarding against SSRF and overflow."""
    from datetime import UTC
    from urllib.parse import urlparse

    from truthengine.sources.security import validate_dns_ip

    parsed = urlparse(url)
    host = parsed.hostname or ""

    # 1. SSRF check on host DNS
    try:
        validate_dns_ip(host)
    except ValueError as exc:
        return FetchResult(
            url=url,
            fetched_at=datetime.now(UTC),
            success=False,
            http_status=None,
            content_type="",
            title="",
            extracted_text="",
            original_html="",
            content_length=None,
            fetch_duration_ms=0,
            etag=None,
            last_modified=None,
            encoding=None,
            error_type="blocked_host",
            error_message=str(exc),
        )

    # 2. Scheme validation
    if parsed.scheme.lower() not in ("http", "https"):
        return FetchResult(
            url=url,
            fetched_at=datetime.now(UTC),
            success=False,
            http_status=None,
            content_type="",
            title="",
            extracted_text="",
            original_html="",
            content_length=None,
            fetch_duration_ms=0,
            etag=None,
            last_modified=None,
            encoding=None,
            error_type="unsupported_content",
            error_message=f"Unsupported scheme: {parsed.scheme}",
        )

    headers = {"User-Agent": USER_AGENT}
    start_time = time.perf_counter()

    try:
        with httpx.Client(
            follow_redirects=True,
            max_redirects=5,
            timeout=httpx.Timeout(TIMEOUT),
        ) as client:
            with client.stream("GET", url, headers=headers) as response:
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                # Validate content-type
                content_type = response.headers.get("content-type", "").lower()
                allowed_types = (
                    "text/html",
                    "text/plain",
                    "application/xhtml+xml",
                )
                if not any(t in content_type for t in allowed_types):
                    return FetchResult(
                        url=url,
                        fetched_at=datetime.now(UTC),
                        success=False,
                        http_status=response.status_code,
                        content_type=content_type,
                        title="",
                        extracted_text="",
                        original_html="",
                        content_length=None,
                        fetch_duration_ms=duration_ms,
                        etag=response.headers.get("etag"),
                        last_modified=None,
                        encoding=response.encoding,
                        error_type="unsupported_content",
                        error_message=f"Unsupported content type: {content_type}",
                    )

                # Read last modified header
                last_mod = None
                last_mod_header = response.headers.get("last-modified")
                if last_mod_header:
                    try:
                        from email.utils import parsedate_to_datetime

                        last_mod = parsedate_to_datetime(last_mod_header)
                    except (ValueError, TypeError):
                        pass

                # Check Content-Length size constraints
                content_length = response.headers.get("content-length")
                expected_len = (
                    int(content_length) if content_length and content_length.isdigit() else None
                )
                if expected_len and expected_len > MAX_RESPONSE_SIZE:
                    return FetchResult(
                        url=url,
                        fetched_at=datetime.now(UTC),
                        success=False,
                        http_status=response.status_code,
                        content_type=content_type,
                        title="",
                        extracted_text="",
                        original_html="",
                        content_length=expected_len,
                        fetch_duration_ms=duration_ms,
                        etag=response.headers.get("etag"),
                        last_modified=last_mod,
                        encoding=response.encoding,
                        error_type="unsupported_content",
                        error_message=f"Content-Length exceeds limit: {expected_len} bytes",
                    )

                # Stream and buffer chunks
                body_bytes = bytearray()
                for chunk in response.iter_bytes(chunk_size=8192):
                    body_bytes.extend(chunk)
                    if len(body_bytes) > MAX_RESPONSE_SIZE:
                        return FetchResult(
                            url=url,
                            fetched_at=datetime.now(UTC),
                            success=False,
                            http_status=response.status_code,
                            content_type=content_type,
                            title="",
                            extracted_text="",
                            original_html="",
                            content_length=len(body_bytes),
                            fetch_duration_ms=duration_ms,
                            etag=response.headers.get("etag"),
                            last_modified=last_mod,
                            encoding=response.encoding,
                            error_type="unsupported_content",
                            error_message="Response size exceeded 5 MB limit",
                        )

                # Decode textual payload
                raw_html = body_bytes.decode(response.encoding or "utf-8", errors="replace")

                # Extract readable content with trafilatura first. BeautifulSoup
                # remains as a deterministic fallback for sparse pages.
                soup = BeautifulSoup(raw_html, "html.parser")
                title = (soup.title.string or "").strip() if soup.title else ""
                if not title:
                    title = f"Snapshot of {host}"

                extracted_text = trafilatura.extract(
                    raw_html,
                    url=url,
                    include_comments=False,
                    include_tables=True,
                    output_format="txt",
                )
                if not extracted_text:
                    for script_or_style in soup(["script", "style", "head", "meta", "link"]):
                        script_or_style.decompose()
                    extracted_text = soup.get_text(separator="\n")

                lines = (line.strip() for line in extracted_text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                extracted_text = "\n".join(chunk for chunk in chunks if chunk)

                return FetchResult(
                    url=url,
                    fetched_at=datetime.now(UTC),
                    success=True,
                    http_status=response.status_code,
                    content_type=content_type,
                    title=title,
                    extracted_text=extracted_text,
                    original_html=raw_html,
                    content_length=len(body_bytes),
                    fetch_duration_ms=duration_ms,
                    etag=response.headers.get("etag"),
                    last_modified=last_mod,
                    encoding=response.encoding,
                    error_type=None,
                    error_message=None,
                )

    except httpx.ConnectTimeout as exc:
        return FetchResult(
            url=url,
            fetched_at=datetime.now(UTC),
            success=False,
            http_status=None,
            content_type="",
            title="",
            extracted_text="",
            original_html="",
            content_length=None,
            fetch_duration_ms=int((time.perf_counter() - start_time) * 1000),
            etag=None,
            last_modified=None,
            encoding=None,
            error_type="timeout",
            error_message=f"Connection timed out: {exc}",
        )
    except httpx.ReadTimeout as exc:
        return FetchResult(
            url=url,
            fetched_at=datetime.now(UTC),
            success=False,
            http_status=None,
            content_type="",
            title="",
            extracted_text="",
            original_html="",
            content_length=None,
            fetch_duration_ms=int((time.perf_counter() - start_time) * 1000),
            etag=None,
            last_modified=None,
            encoding=None,
            error_type="timeout",
            error_message=f"Read timed out: {exc}",
        )
    except httpx.TooManyRedirects as exc:
        return FetchResult(
            url=url,
            fetched_at=datetime.now(UTC),
            success=False,
            http_status=None,
            content_type="",
            title="",
            extracted_text="",
            original_html="",
            content_length=None,
            fetch_duration_ms=int((time.perf_counter() - start_time) * 1000),
            etag=None,
            last_modified=None,
            encoding=None,
            error_type="redirect_loop",
            error_message=f"Redirect loop detected: {exc}",
        )
    except httpx.ConnectError as exc:
        err_str = str(exc).lower()
        err_type = (
            "ssl"
            if "ssl" in err_str or "tls" in err_str
            else "dns"
            if "getaddrinfo" in err_str
            or "name or service not known" in err_str
            or "name resolution" in err_str
            else "dns"
        )
        return FetchResult(
            url=url,
            fetched_at=datetime.now(UTC),
            success=False,
            http_status=None,
            content_type="",
            title="",
            extracted_text="",
            original_html="",
            content_length=None,
            fetch_duration_ms=int((time.perf_counter() - start_time) * 1000),
            etag=None,
            last_modified=None,
            encoding=None,
            error_type=err_type,
            error_message=f"Connection/DNS fault: {exc}",
        )
    except httpx.RequestError as exc:
        return FetchResult(
            url=url,
            fetched_at=datetime.now(UTC),
            success=False,
            http_status=None,
            content_type="",
            title="",
            extracted_text="",
            original_html="",
            content_length=None,
            fetch_duration_ms=int((time.perf_counter() - start_time) * 1000),
            etag=None,
            last_modified=None,
            encoding=None,
            error_type="dns",
            error_message=f"HTTPX request failed: {exc}",
        )
