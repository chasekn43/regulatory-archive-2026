"""
Perplexity Search API Integration Module.

Provides programmatic web search capabilities using the official Perplexity Search API
(POST https://api.perplexity.ai/search) with full support for:
- Single string or multi-query search (up to 5 queries per request)
- URL-based deduplication across multi-query responses
- Domain allowlisting / denylisting (search_domain_filter)
- Recency and date filters (search_recency_filter, search_after_date_filter, etc.)
- Regionalization via ISO 3166-1 alpha-2 country codes
- Search context size extraction control ('low', 'medium', 'high')
- Robust error handling (401 Auth, 429 Rate Limits with Retry-After, 422 Validation)

Security note: The API key is resolved from the PERPLEXITY_API_KEY environment variable.
Never hardcode, print, or commit API keys.
"""

from __future__ import annotations

import os
import sys
import json
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict, dataclass

# Attempt import of official SDK
try:
    from perplexity import Perplexity
    HAS_SDK = True
except ImportError:
    HAS_SDK = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

SEARCH_ENDPOINT = "https://api.perplexity.ai/search"


@dataclass
class SearchResult:
    """Represents a single ranked search result item."""
    title: str
    url: str
    snippet: str
    date: Optional[str] = None
    last_updated: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchResponse:
    """Represents the structured response from the Perplexity Search API."""
    results: List[SearchResult]
    query: Union[str, List[str]]
    id: Optional[str] = None
    server_time: Optional[str] = None
    total_results: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "total_results": len(self.results),
            "server_time": self.server_time,
            "results": [r.to_dict() for r in self.results]
        }


def normalize_url(url: str) -> str:
    """Normalize a URL for accurate deduplication."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        # Normalize scheme and netloc to lowercase, strip default ports and trailing slash
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/")
        # Rebuild URL without fragment/tracking hash
        normalized = urllib.parse.urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
        return normalized
    except Exception:
        return url.strip().rstrip("/")


def deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
    """Deduplicate a list of SearchResult items based on normalized URL, preserving rank order."""
    seen_urls = set()
    deduped = []
    for r in results:
        norm = normalize_url(r.url)
        if norm and norm not in seen_urls:
            seen_urls.add(norm)
            deduped.append(r)
    return deduped


def get_api_key() -> str:
    """
    Resolve the Perplexity API key from environment variables or local fallback.
    Never prints or logs the actual key.
    """
    key = os.environ.get("PERPLEXITY_API_KEY")
    if key and key.strip():
        return key.strip()

    # Check local IDE config if available in dev environment
    mcp_path = os.path.expanduser(r"~\.gemini\config\mcp_config.json")
    if os.path.exists(mcp_path):
        try:
            with open(mcp_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                env_key = cfg.get("mcpServers", {}).get("perplexity-ask", {}).get("env", {}).get("PERPLEXITY_API_KEY")
                if env_key and env_key.strip():
                    return env_key.strip()
        except Exception:
            pass

    raise ValueError(
        "PERPLEXITY_API_KEY is not set. Please obtain an API key from the "
        "Perplexity API Console (https://console.perplexity.ai) and export it: "
        "export PERPLEXITY_API_KEY='your_key_here' (or $env:PERPLEXITY_API_KEY='...' in PowerShell)."
    )


class PerplexitySearchClient:
    """
    High-level client for the Perplexity Search API.
    Supports official SDK and direct HTTP transports with robust error handling.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or get_api_key()
        self._sdk_client: Optional[Any] = None
        if HAS_SDK:
            try:
                self._sdk_client = Perplexity(api_key=self._api_key)
            except Exception:
                self._sdk_client = None

    def search(
        self,
        query: Union[str, List[str]],
        max_results: int = 10,
        search_context_size: str = "high",
        country: Optional[str] = None,
        search_domain_filter: Optional[List[str]] = None,
        search_language_filter: Optional[List[str]] = None,
        search_recency_filter: Optional[str] = None,
        search_after_date_filter: Optional[str] = None,
        search_before_date_filter: Optional[str] = None,
        last_updated_after_filter: Optional[str] = None,
        last_updated_before_filter: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_tokens_per_page: Optional[int] = None,
        dedupe: bool = True
    ) -> SearchResponse:
        """
        Execute a search request against the Perplexity Search API.

        Args:
            query: Single string or list of up to 5 queries.
            max_results: Maximum results to return (1-20, default 10).
            search_context_size: 'low', 'medium', or 'high' (default 'high').
            country: ISO 3166-1 alpha-2 country code (e.g. 'US').
            search_domain_filter: List of up to 20 domains (allowlist or denylist with '-').
            search_language_filter: List of ISO 639-1 language codes (e.g. ['en']).
            search_recency_filter: 'hour', 'day', 'week', 'month', or 'year'.
            search_after_date_filter: Published after date ('MM/DD/YYYY').
            search_before_date_filter: Published before date ('MM/DD/YYYY').
            last_updated_after_filter: Updated after date ('MM/DD/YYYY').
            last_updated_before_filter: Updated before date ('MM/DD/YYYY').
            max_tokens: Optional token cap across all results.
            max_tokens_per_page: Optional token cap per page.
            dedupe: Whether to deduplicate results by URL (default True).

        Returns:
            SearchResponse containing ranked SearchResult objects.
        """
        # Validate query constraints
        if isinstance(query, list):
            if len(query) == 0:
                raise ValueError("Query list cannot be empty.")
            if len(query) > 5:
                raise ValueError("Perplexity Search API supports a maximum of 5 queries per request.")
        elif not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string or list of strings.")

        # Clamp max_results between 1 and 20
        max_results = max(1, min(20, max_results))

        # Build payload dictionary for Search API
        payload: Dict[str, Any] = {
            "query": query,
            "max_results": max_results,
        }

        if search_context_size and not (max_tokens or max_tokens_per_page):
            payload["search_context_size"] = search_context_size
        if country:
            payload["country"] = country.strip().upper()
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter[:20]
        if search_language_filter:
            payload["search_language_filter"] = search_language_filter[:20]
        if search_recency_filter:
            payload["search_recency_filter"] = search_recency_filter
        if search_after_date_filter:
            payload["search_after_date_filter"] = search_after_date_filter
        if search_before_date_filter:
            payload["search_before_date_filter"] = search_before_date_filter
        if last_updated_after_filter:
            payload["last_updated_after_filter"] = last_updated_after_filter
        if last_updated_before_filter:
            payload["last_updated_before_filter"] = last_updated_before_filter
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if max_tokens_per_page:
            payload["max_tokens_per_page"] = max_tokens_per_page

        # Execute via SDK if available
        if self._sdk_client is not None:
            try:
                sdk_resp = self._sdk_client.search.create(**payload)
                raw_results = []
                for item in getattr(sdk_resp, "results", []):
                    raw_results.append(
                        SearchResult(
                            title=getattr(item, "title", ""),
                            url=getattr(item, "url", ""),
                            snippet=getattr(item, "snippet", ""),
                            date=getattr(item, "date", None),
                            last_updated=getattr(item, "last_updated", None)
                        )
                    )
                
                final_results = deduplicate_results(raw_results) if dedupe else raw_results
                return SearchResponse(
                    results=final_results,
                    query=query,
                    id=getattr(sdk_resp, "id", None),
                    server_time=getattr(sdk_resp, "server_time", None),
                    total_results=len(final_results)
                )
            except Exception:
                # If SDK fails, fall back to direct HTTP transport
                pass

        # Direct HTTP Transport Execution
        return self._http_search(payload, query=query, dedupe=dedupe)

    def _http_search(self, payload: Dict[str, Any], query: Union[str, List[str]], dedupe: bool) -> SearchResponse:
        """Direct HTTP implementation with rate limit handling and retries."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": "KinslowRegulatoryArchive-PerplexityClient/1.0"
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if HAS_HTTPX:
                    with httpx.Client(timeout=20.0) as client:
                        resp = client.post(SEARCH_ENDPOINT, json=payload, headers=headers)
                        status_code = resp.status_code
                        headers_dict = dict(resp.headers)
                        resp_data = resp.json() if status_code == 200 else {}
                else:
                    import urllib.request
                    import urllib.error
                    req_data = json.dumps(payload).encode("utf-8")
                    req = urllib.request.Request(SEARCH_ENDPOINT, data=req_data, headers=headers, method="POST")
                    try:
                        with urllib.request.urlopen(req, timeout=20.0) as http_resp:
                            status_code = http_resp.status
                            headers_dict = dict(http_resp.headers)
                            resp_data = json.loads(http_resp.read().decode("utf-8"))
                    except urllib.error.HTTPError as http_err:
                        status_code = http_err.code
                        headers_dict = dict(http_err.headers)
                        resp_data = json.loads(http_err.read().decode("utf-8"))

                if status_code == 200:
                    raw_results = [
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            date=item.get("date"),
                            last_updated=item.get("last_updated")
                        )
                        for item in resp_data.get("results", [])
                    ]
                    final_results = deduplicate_results(raw_results) if dedupe else raw_results
                    return SearchResponse(
                        results=final_results,
                        query=query,
                        id=resp_data.get("id"),
                        server_time=resp_data.get("server_time"),
                        total_results=len(final_results)
                    )

                if status_code == 401:
                    raise PermissionError(
                        "Perplexity Search API returned HTTP 401 Unauthorized. "
                        "Please verify your PERPLEXITY_API_KEY."
                    )

                if status_code == 429:
                    retry_after = int(headers_dict.get("retry-after", headers_dict.get("Retry-After", "2")))
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue
                    raise RuntimeError(f"Perplexity Search API rate limit exceeded (HTTP 429). Retry after {retry_after}s.")

                if status_code == 422:
                    raise ValueError(f"Perplexity Search API validation error (HTTP 422): {json.dumps(resp_data)}")

                raise RuntimeError(f"Perplexity Search API returned HTTP {status_code}: {resp_data}")

            except (PermissionError, ValueError, RuntimeError):
                raise
            except Exception as exc:
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise RuntimeError(f"Network error communicating with Perplexity Search API: {exc}") from exc

        raise RuntimeError("Failed to complete Perplexity Search request after multiple retries.")


# Convenience function for quick functional imports
def search_web(
    query: Union[str, List[str]],
    max_results: int = 10,
    search_context_size: str = "high",
    country: Optional[str] = None,
    search_domain_filter: Optional[List[str]] = None,
    search_recency_filter: Optional[str] = None,
    api_key: Optional[str] = None
) -> SearchResponse:
    """
    Search the web using Perplexity Search API and return structured results.
    """
    client = PerplexitySearchClient(api_key=api_key)
    return client.search(
        query=query,
        max_results=max_results,
        search_context_size=search_context_size,
        country=country,
        search_domain_filter=search_domain_filter,
        search_recency_filter=search_recency_filter
    )


def main():
    """CLI Entry point for terminal-based search audits."""
    if len(sys.argv) < 2:
        print("Usage: python perplexity_search.py <query> [--max-results N] [--country US] [--domain DOMAIN]")
        print("Example: python perplexity_search.py \"CFPB buy now pay later dispute rules\" --max-results 5")
        sys.exit(1)

    query_arg = sys.argv[1]
    max_res = 10
    country_arg = None
    domains = None

    idx = 2
    while idx < len(sys.argv):
        if sys.argv[idx] == "--max-results" and idx + 1 < len(sys.argv):
            max_res = int(sys.argv[idx + 1])
            idx += 2
        elif sys.argv[idx] == "--country" and idx + 1 < len(sys.argv):
            country_arg = sys.argv[idx + 1]
            idx += 2
        elif sys.argv[idx] == "--domain" and idx + 1 < len(sys.argv):
            domains = [sys.argv[idx + 1]]
            idx += 2
        else:
            idx += 1

    try:
        client = PerplexitySearchClient()
        response = client.search(
            query=query_arg,
            max_results=max_res,
            country=country_arg,
            search_domain_filter=domains
        )

        print(f"\n=======================================================")
        print(f"PERPLEXITY SEARCH API RESULTS ({len(response.results)} returned)")
        print(f"Query: {query_arg}")
        print(f"=======================================================\n")

        for i, res in enumerate(response.results, 1):
            print(f"[{i}] {res.title}")
            print(f"    URL: {res.url}")
            if res.date:
                print(f"    Date: {res.date} | Last Updated: {res.last_updated or 'N/A'}")
            print(f"    Snippet: {res.snippet[:180]}...\n")

    except Exception as err:
        print(f"Search failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
