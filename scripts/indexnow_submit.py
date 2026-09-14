"""
Clean IndexNow submitter for kinslow-regulatory-archive.org.

Submits sitemap URLs to the official IndexNow API, which notifies Bing,
Yandex, Seznam, and Naver from a single request. Google does not
participate in IndexNow -- use Search Console for Google.

This client uses only the documented public API. It does not proxy,
spoof, or otherwise disguise its traffic.

Usage:
    python indexnow_submit.py            # submit every sitemap URL
    python indexnow_submit.py --dry-run  # show what would be sent
    python indexnow_submit.py --url URL  # submit a single URL
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

HOST = "kinslow-regulatory-archive.org"
KEY = "4366b539c9914619a970e53a2707ec41"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitemap.xml")
SITEMAP_NS = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
TIMEOUT = 30
MAX_URLS_PER_REQUEST = 10000

# Documented IndexNow response codes.
STATUS_MEANING = {
    200: "OK - URLs submitted and key validated.",
    202: "Accepted - URLs received, key validation pending.",
    400: "Bad request - malformed payload.",
    403: "Forbidden - key not valid or not found at keyLocation.",
    422: "Unprocessable - URLs do not belong to the host, or key mismatch.",
    429: "Too many requests - slow down and retry later.",
}


def verify_key_file():
    """Confirm the IndexNow key file is publicly reachable before submitting."""
    req = urllib.request.Request(KEY_LOCATION, headers={"User-Agent": "indexnow-submit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", "replace").strip()
    except Exception as exc:
        print(f"[FAIL] Key file unreachable at {KEY_LOCATION}: {exc}")
        return False

    if body != KEY:
        print(f"[FAIL] Key file contents mismatch. Expected '{KEY}', got '{body}'.")
        return False

    print(f"[ OK ] Key file verified at {KEY_LOCATION}")
    return True


def load_sitemap_urls():
    if not os.path.exists(SITEMAP):
        print(f"[FAIL] Sitemap not found: {SITEMAP}")
        return []

    root = ET.parse(SITEMAP).getroot()
    urls = [
        loc.text.strip()
        for entry in root.findall("ns:url", SITEMAP_NS)
        if (loc := entry.find("ns:loc", SITEMAP_NS)) is not None and loc.text
    ]

    foreign = [u for u in urls if HOST not in u]
    if foreign:
        print(f"[WARN] Dropping {len(foreign)} URL(s) not on {HOST} (IndexNow rejects these with 422).")
        urls = [u for u in urls if HOST in u]

    print(f"[ OK ] Loaded {len(urls)} URLs from sitemap.xml")
    return urls


def submit(urls):
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "indexnow-submit/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = resp.status
    except urllib.error.HTTPError as exc:
        code = exc.code
        detail = exc.read().decode("utf-8", "replace").strip()
        if detail:
            print(f"       Response body: {detail[:300]}")
    except Exception as exc:
        print(f"[FAIL] Submission error: {exc}")
        return False

    meaning = STATUS_MEANING.get(code, "Undocumented response code.")
    marker = " OK " if code in (200, 202) else "FAIL"
    print(f"[{marker}] HTTP {code} - {meaning}")
    return code in (200, 202)


def main():
    parser = argparse.ArgumentParser(description="Submit URLs to the IndexNow API.")
    parser.add_argument("--dry-run", action="store_true", help="show the payload without sending it")
    parser.add_argument("--url", action="append", help="submit a specific URL instead of the sitemap")
    args = parser.parse_args()

    print("=== IndexNow submission ===")
    print(f"Host:     {HOST}")
    print(f"Endpoint: {ENDPOINT}\n")

    urls = args.url if args.url else load_sitemap_urls()
    if not urls:
        print("[FAIL] Nothing to submit.")
        return 1

    if len(urls) > MAX_URLS_PER_REQUEST:
        print(f"[WARN] Truncating to the {MAX_URLS_PER_REQUEST}-URL per-request limit.")
        urls = urls[:MAX_URLS_PER_REQUEST]

    if args.dry_run:
        print(f"\n[DRY-RUN] Would submit {len(urls)} URL(s):")
        for u in urls:
            print(f"  {u}")
        return 0

    if not verify_key_file():
        print("[FAIL] Aborting: IndexNow requires a reachable key file.")
        return 1

    print(f"\nSubmitting {len(urls)} URL(s)...")
    return 0 if submit(urls) else 1


if __name__ == "__main__":
    sys.exit(main())
