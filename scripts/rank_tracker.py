"""
Search visibility tracker for kinslow-regulatory-archive.org.

Pulls real ranking data from the official webmaster APIs instead of
scraping search engine result pages:

  * Google  -> Search Console Search Analytics API
  * Bing    -> Bing Webmaster Tools API

Bing's index also serves DuckDuckGo, Yahoo and Ecosia web results, so
the Bing figures below effectively cover those engines too. There is no
DuckDuckGo or Yahoo webmaster API to query, and scraping them is both
blocked (403) and unnecessary: if you rank in Bing, you rank in DDG.

Both report actual impressions, clicks, CTR and average position for the
queries your site genuinely ranks on. That is ground truth from the
engine, and it is strictly better data than a parsed SERP.

Credentials
-----------
Google : service account JSON at GSC_KEY_FILE (default google_console_key.json).
         The service account email must be added to the Search Console
         property under Settings -> Users and permissions.
Bing   : API key in the BING_WEBMASTER_API_KEY environment variable
         (or a .env file alongside this script). Optional - skipped if absent.

Usage
-----
    python rank_tracker.py                 # last 28 days
    python rank_tracker.py --days 7
    python rank_tracker.py --check-auth    # verify credentials only
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "sc-domain:kinslow-regulatory-archive.org"
BING_SITE = "https://kinslow-regulatory-archive.org"
GSC_KEY_FILE = os.environ.get("GSC_KEY_FILE", os.path.join(HERE, "google_console_key.json"))
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# keywords_search.txt holds real consumer search phrases and is the primary
# bank. The legacy files hold site: operator strings, which no one searches;
# strip_operators() rewrites them into plausible queries so they can match.
KEYWORD_FILES = ["keywords_search.txt", "keywords.txt", "keywords_targeted.txt"]
QUERY_BANK = "archive_200_queries.json"
OUT_JSON = os.path.join(HERE, "rank_tracking_results.json")
OUT_MD = os.path.join(HERE, "rank_tracking_report.md")

# GSC caps a single Search Analytics response at 25k rows.
GSC_ROW_LIMIT = 25000
# GSC data lags roughly 2-3 days; skip the freshest days to avoid partial rows.
GSC_LAG_DAYS = 3


def load_env_file():
    """Load simple KEY=value pairs from a local .env, without overriding real env vars."""
    path = os.path.join(HERE, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def strip_operators(term):
    """Turn a site-search operator string into the phrase a person would type.

    The legacy keyword files prefix every entry with the bare domain and wrap
    fragments in quotes. Search engines never report those as queries, so the
    prefix and quoting are removed before the term enters the tracked bank.
    """
    cleaned = re.sub(r"\bkinslow-regulatory-archive\.org\b", " ", term, flags=re.I)
    cleaned = re.sub(r"\b(?:site|inurl|intitle|intext|filetype):\S*", " ", cleaned, flags=re.I)
    cleaned = cleaned.replace('"', " ").replace("'", " ")
    return re.sub(r"\s+", " ", cleaned).strip(" -|")


def load_tracked_terms():
    """Collect the tracked keyword and query bank, de-duplicated, order preserved."""
    terms, seen = [], set()

    for name in KEYWORD_FILES:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                term = strip_operators(line.strip())
                if len(term) < 3:
                    continue
                if term and not term.startswith("#") and term.lower() not in seen:
                    seen.add(term.lower())
                    terms.append(term)

    bank = os.path.join(HERE, QUERY_BANK)
    if os.path.exists(bank):
        try:
            with open(bank, encoding="utf-8") as fh:
                data = json.load(fh)
            queries = data.get("queries", []) if isinstance(data, dict) else data
            for q in queries:
                q = (q or "").strip()
                if q and q.lower() not in seen:
                    seen.add(q.lower())
                    terms.append(q)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[WARN] Could not read {QUERY_BANK}: {exc}")

    return terms


# Tokens that carry no ranking signal: site-scoped scraper operators, boilerplate
# and stopwords. Tracked terms in this repo were written as scraper probes
# ("kinslow-regulatory-archive.org \"Chase Kinslow\" Affirm dispute"), so the
# domain and operator noise has to come off before anything can match a real
# user query pulled from Search Console.
STOPWORDS = {
    "the", "a", "an", "of", "on", "in", "to", "for", "and", "or", "is", "are",
    "was", "were", "be", "by", "with", "from", "at", "as", "it", "that", "this",
    "you", "your", "my", "me", "more", "about", "org", "com", "www", "http",
    "https", "site", "kinslow", "regulatory", "archive",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_tokens(text):
    """Reduce a term or query to comparable significant tokens."""
    text = text.lower()
    text = text.replace("kinslow-regulatory-archive.org", " ")
    tokens = TOKEN_RE.findall(text)
    out = set()
    for t in tokens:
        if t in STOPWORDS or len(t) <= 1:
            continue
        # Light singular/plural folding so "disputes" matches "dispute".
        if len(t) > 3 and t.endswith("es") and not t.endswith("ses"):
            t = t[:-2]
        elif len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.add(t)
    return out


def gsc_service():
    """Build an authenticated Search Console client, or return None with a reason."""
    if not os.path.exists(GSC_KEY_FILE):
        print(f"[SKIP] Google: service account key not found at {GSC_KEY_FILE}")
        return None
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("[SKIP] Google: pip install google-api-python-client google-auth")
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(GSC_KEY_FILE, scopes=SCOPES)
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    except Exception as exc:
        print(f"[SKIP] Google: could not authenticate ({exc})")
        return None


def fetch_google(service, days):
    """Pull per-query performance rows plus true site totals from Search Console."""
    end = dt.date.today() - dt.timedelta(days=GSC_LAG_DAYS)
    start = end - dt.timedelta(days=days)
    window = {"startDate": start.isoformat(), "endDate": end.isoformat()}

    # Undimensioned totals first. Google withholds rare queries for privacy, so
    # summing the query dimension understates real traffic -- often severely.
    try:
        totals_resp = service.searchanalytics().query(
            siteUrl=SITE_URL, body={**window, "rowLimit": 1}
        ).execute()
    except Exception as exc:
        msg = str(exc)
        if "does not own" in msg or "403" in msg:
            print("[FAIL] Google: 403 - the service account is not a user on this property.")
            print("       Add its client_email in Search Console -> Settings -> Users and permissions.")
        else:
            print(f"[FAIL] Google Search Console query failed: {exc}")
        return None

    t = (totals_resp.get("rows") or [{}])[0]
    totals = {
        "clicks": t.get("clicks", 0),
        "impressions": t.get("impressions", 0),
        "position": round(t.get("position", 0.0), 1),
    }

    try:
        resp = service.searchanalytics().query(
            siteUrl=SITE_URL, body={**window, "dimensions": ["query"], "rowLimit": GSC_ROW_LIMIT}
        ).execute()
    except Exception as exc:
        print(f"[FAIL] Google query-dimension request failed: {exc}")
        return None

    rows = [
        {
            "query": r["keys"][0],
            "clicks": r.get("clicks", 0),
            "impressions": r.get("impressions", 0),
            "ctr": round(r.get("ctr", 0.0) * 100, 2),
            "position": round(r.get("position", 0.0), 1),
        }
        for r in resp.get("rows", [])
    ]

    visible_impr = sum(r["impressions"] for r in rows)
    hidden = totals["impressions"] - visible_impr
    pct = round(hidden / totals["impressions"] * 100) if totals["impressions"] else 0

    # The page dimension is not privacy-filtered the way queries are, so it
    # recovers the clicks that anonymized queries hide and shows which pages
    # actually earn them.
    pages = []
    try:
        page_resp = service.searchanalytics().query(
            siteUrl=SITE_URL, body={**window, "dimensions": ["page"], "rowLimit": 1000}
        ).execute()
        pages = [
            {
                "page": r["keys"][0],
                "clicks": r.get("clicks", 0),
                "impressions": r.get("impressions", 0),
                "position": round(r.get("position", 0.0), 1),
            }
            for r in page_resp.get("rows", [])
        ]
    except Exception as exc:
        print(f"[WARN] Google page-dimension request failed: {exc}")

    print(f"[ OK ] Google: {totals['clicks']} clicks, {totals['impressions']} impressions ({start} to {end})")
    print(f"       {len(rows)} queries visible; {hidden} impressions ({pct}%) withheld by privacy filtering")
    if pages:
        page_clicks = sum(p["clicks"] for p in pages)
        print(f"       {len(pages)} pages with traffic; {page_clicks} of {totals['clicks']} clicks attributed by page")

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "totals": totals,
        "hidden_impressions": hidden,
        "hidden_pct": pct,
        "rows": rows,
        "pages": pages,
    }


def fetch_bing(days):
    """Pull per-query stats from Bing Webmaster Tools, if an API key is configured."""
    api_key = os.environ.get("BING_WEBMASTER_API_KEY") or os.environ.get("BING_API_KEY")
    if not api_key or api_key.startswith("replace-with"):
        print("[SKIP] Bing: set BING_WEBMASTER_API_KEY to include Bing data.")
        return None

    url = (
        "https://ssl.bing.com/webmaster/api.svc/json/GetQueryStats"
        f"?siteUrl={urllib.parse.quote(BING_SITE, safe='')}&apikey={urllib.parse.quote(api_key)}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "rank-tracker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        print(f"[FAIL] Bing: HTTP {exc.code} - verify the API key and that the site is verified.")
        return None
    except Exception as exc:
        print(f"[FAIL] Bing: {exc}")
        return None

    rows = [
        {
            "query": e.get("Query", ""),
            "clicks": e.get("Clicks", 0),
            "impressions": e.get("Impressions", 0),
            "position": e.get("AvgClickPosition", 0),
        }
        for e in payload.get("d", []) or []
    ]
    print(f"[ OK ] Bing: {len(rows)} ranking queries")
    return {"rows": rows}


MATCH_THRESHOLD = 0.6
MIN_TOKEN_OVERLAP = 2


def match_tracked(rows, terms):
    """Associate each real Search Console query with at most one tracked term.

    Exact string matching never worked here: the tracked bank is made of
    site-scoped scraper probes, while Search Console returns what humans
    actually typed. Matching is done on significant-token overlap, but it is
    deliberately conservative -- a single shared word like "affirm" is not a
    match, and each real query claims only its single best term. Anything that
    fails to clear the bar is surfaced as an untracked query instead, which is
    the more actionable result.
    """
    prepared = [(term, normalize_tokens(term)) for term in terms]
    tracked, claimed_terms = [], set()

    for row in rows:
        r_tokens = normalize_tokens(row["query"])
        if not r_tokens:
            continue

        best, best_score, best_overlap = None, 0.0, 0
        for term, t_tokens in prepared:
            if not t_tokens:
                continue
            overlap = len(t_tokens & r_tokens)
            if overlap < min(MIN_TOKEN_OVERLAP, len(r_tokens)):
                continue
            score = overlap / min(len(t_tokens), len(r_tokens))
            if score > best_score:
                best, best_score, best_overlap = term, score, overlap

        if best and best_score >= MATCH_THRESHOLD:
            hit = dict(row)
            hit["tracked_term"] = best
            hit["match_score"] = round(best_score, 2)
            tracked.append(hit)
            claimed_terms.add(best)

    discovered = [r for r in rows if r["query"] not in {t["query"] for t in tracked}]
    missing = [{"query": t, "position": None} for t in terms if t not in claimed_terms]
    return tracked, missing, discovered


def write_report(results, terms):
    google = results.get("google")
    rows = google["rows"] if google else []
    tracked, missing, discovered = match_tracked(rows, terms) if google else ([], [], [])

    lines = [
        "# Search Visibility Report",
        "",
        f"Generated: {results['generated_at']}",
        f"Source: official webmaster APIs (no SERP scraping)",
        "",
    ]

    if google:
        ranking = sorted([r for r in tracked if r.get("position")], key=lambda r: r["position"])
        totals = google.get("totals", {})
        lines += [
            "## Google Search Console",
            "",
            f"- Window: {google['start']} to {google['end']}",
            f"- **Site totals: {totals.get('clicks', 0)} clicks, "
            f"{totals.get('impressions', 0)} impressions, "
            f"avg position {totals.get('position', 0)}**",
            f"- Queries visible at query level: **{len(rows)}**",
            f"- Impressions withheld by Google's privacy filter: "
            f"**{google.get('hidden_impressions', 0)} ({google.get('hidden_pct', 0)}%)**",
            f"- Tracked terms ranking: **{len(ranking)}** of {len(terms)}",
            "",
            "> Google anonymizes rare queries, so the per-query table below does not",
            "> sum to the site totals. Trust the totals for performance; use the table",
            "> for which specific terms are surfacing.",
            "",
        ]
        if ranking:
            lines += [
                "### Tracked terms currently ranking",
                "",
                "| Real query | Matched tracked term | Position | Impressions | Clicks |",
                "|---|---|---|---|---|",
            ]
            lines += [
                f"| {r['query']} | {(r.get('tracked_term') or '')[:70]} | "
                f"{r['position']} | {r['impressions']} | {r['clicks']} |"
                for r in ranking[:50]
            ]
            lines.append("")
        if discovered:
            top = sorted(discovered, key=lambda r: -r["impressions"])[:25]
            lines += [
                "### Untracked queries you rank for (consider adding)",
                "",
                "| Query | Position | Impressions |",
                "|---|---|---|",
            ]
            lines += [f"| {r['query']} | {r['position']} | {r['impressions']} |" for r in top]
            lines.append("")
        lines += [f"- Tracked terms with no impressions yet: **{len(missing)}**", ""]

        pages = google.get("pages") or []
        if pages:
            top = sorted(pages, key=lambda p: (-p["clicks"], -p["impressions"]))[:15]
            lines += [
                "### Pages earning traffic (recovers the privacy-filtered clicks)",
                "",
                "| Page | Clicks | Impressions | Avg position |",
                "|---|---|---|---|",
            ]
            for p in top:
                path = p["page"].replace("https://kinslow-regulatory-archive.org", "") or "/"
                lines.append(f"| {path} | {p['clicks']} | {p['impressions']} | {p['position']} |")
            lines.append("")
    else:
        lines += ["## Google Search Console", "", "_No data - credentials unavailable._", ""]

    bing = results.get("bing")
    if bing:
        rows_b = bing["rows"]
        clicks_b = sum(r.get("clicks", 0) for r in rows_b)
        impr_b = sum(r.get("impressions", 0) for r in rows_b)
        lines += [
            "## Bing Webmaster Tools",
            "",
            "_Bing's index also serves DuckDuckGo, Yahoo and Ecosia web results,_",
            "_so these figures effectively cover those engines as well._",
            "",
            f"- Ranking queries: **{len(rows_b)}**",
            f"- Total clicks: **{clicks_b}** / impressions: **{impr_b}**",
            "",
        ]
        if rows_b:
            top_b = sorted(rows_b, key=lambda r: -r.get("impressions", 0))[:25]
            lines += ["| Query | Impressions | Clicks |", "|---|---|---|"]
            lines += [
                f"| {r['query']} | {r.get('impressions', 0)} | {r.get('clicks', 0)} |"
                for r in top_b
            ]
            lines.append("")
    else:
        lines += ["## Bing Webmaster Tools", "", "_No data - API key not configured._", ""]

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"[ OK ] Report written to {os.path.basename(OUT_MD)}")


def main():
    parser = argparse.ArgumentParser(description="Track search visibility via official webmaster APIs.")
    parser.add_argument("--days", type=int, default=28, help="lookback window in days (default 28)")
    parser.add_argument("--check-auth", action="store_true", help="verify credentials and exit")
    args = parser.parse_args()

    load_env_file()
    print("=== Search visibility tracker ===")
    print(f"Property: {SITE_URL}\n")

    terms = load_tracked_terms()
    print(f"[ OK ] Tracking {len(terms)} keywords and queries")

    service = gsc_service()
    if args.check_auth:
        bing_key = os.environ.get("BING_WEBMASTER_API_KEY") or os.environ.get("BING_API_KEY")
        print(f"\nGoogle credentials: {'present' if service else 'MISSING'}")
        print(f"Bing API key      : {'present' if bing_key else 'MISSING'}")
        return 0 if service else 1

    results = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "property": SITE_URL,
        "tracked_terms": len(terms),
        "google": fetch_google(service, args.days) if service else None,
        "bing": fetch_bing(args.days),
    }

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    print(f"[ OK ] Raw data written to {os.path.basename(OUT_JSON)}")

    write_report(results, terms)
    return 0 if (results["google"] or results["bing"]) else 1


if __name__ == "__main__":
    sys.exit(main())
