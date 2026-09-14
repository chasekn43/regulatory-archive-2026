"""
FireProx Configuration - Centralized proxy URL mapping.

All search/audit scripts import from this module to route requests
through AWS API Gateway proxies with rotating source IPs.

Toggle USE_FIREPROX to False to disable proxying and hit engines directly.
"""
import os

# Master toggle - set to False to bypass all proxies
USE_FIREPROX = os.environ.get("USE_FIREPROX", "true").lower() == "true"

# FireProx API Gateway endpoints (created 2026-08-13)
# Each maps a search engine domain to its rotating-IP proxy
FIREPROX_ENDPOINTS = {
    # Search engines
    "google":       "https://ko8dobd0k9.execute-api.us-east-1.amazonaws.com/fireprox",
    "bing":         "https://iesnyz12gb.execute-api.us-east-1.amazonaws.com/fireprox",
    "yahoo":        "https://5lfgb9vs9d.execute-api.us-east-1.amazonaws.com/fireprox",
    "duckduckgo":   "https://r98spyjrhl.execute-api.us-east-1.amazonaws.com/fireprox",
    "duckduckgo_lite": "https://k65o5d1src.execute-api.us-east-1.amazonaws.com/fireprox",
    # APIs
    "indexnow":     "https://5fa5mq0mqc.execute-api.us-east-1.amazonaws.com/fireprox",
    # Site proxy
    "kinslow_archive": "https://qi6f0n4uz0.execute-api.us-east-1.amazonaws.com/fireprox",
}

# Direct (original) base URLs for each engine
DIRECT_ENDPOINTS = {
    "google":       "https://www.google.com",
    "bing":         "https://www.bing.com",
    "yahoo":        "https://search.yahoo.com",
    "duckduckgo":   "https://html.duckduckgo.com",
    "duckduckgo_lite": "https://lite.duckduckgo.com",
    "indexnow":     "https://api.indexnow.org",
    "kinslow_archive": "https://kinslow-regulatory-archive.org",
}


def get_base_url(engine: str) -> str:
    """Return the base URL for an engine, proxied through FireProx if enabled.

    Usage:
        from fireprox_config import get_base_url
        url = f"{get_base_url('google')}/search?q=test"
    """
    if USE_FIREPROX and engine in FIREPROX_ENDPOINTS:
        return FIREPROX_ENDPOINTS[engine]
    return DIRECT_ENDPOINTS.get(engine, "")


def get_bing_indexnow_url() -> str:
    """Return Bing's IndexNow endpoint (uses Bing proxy if enabled)."""
    if USE_FIREPROX:
        return f"{FIREPROX_ENDPOINTS['bing']}/indexnow"
    return "https://www.bing.com/indexnow"
