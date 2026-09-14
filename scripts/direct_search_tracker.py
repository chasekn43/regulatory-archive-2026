import urllib.request
import urllib.parse
import re
import json
import sys
import time
import random
from html import unescape
from fireprox_config import get_base_url
from waf_bypass_headers import apply_bypass_headers

# Target indicators to match in results
TARGET_INDICATORS = [
    "kinslow-regulatory-archive.org",
    "chasekn43",
    "regulatory-archive-2026",
    "regulatory-archive.kinslow.co",
    "kinslow.co",
    "kinslow",
    "260717-35668593",
    "26-29572"
]

def clean_text(html_str):
    if not html_str:
        return ""
    cleanr = re.compile(r'<.*?>')
    cleantext = re.sub(cleanr, '', html_str)
    return unescape(cleantext).strip()

def decode_url(url):
    try:
        url = unescape(url)
        if "uddg=" in url:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if "uddg" in parsed:
                return parsed["uddg"][0]
        if "r.search.yahoo.com" in url and "/RU=" in url:
            match = re.search(r'/RU=([^/]+)/', url)
            if match:
                return urllib.parse.unquote(match.group(1))
        # Bing /ck/a redirection base64 decoding
        if "bing.com/ck/a" in url or "/ck/a?!" in url:
            clean_url = url.replace("&amp;", "&")
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(clean_url).query)
            if "u" in parsed:
                u_val = parsed["u"][0]
                if len(u_val) > 2:
                    b64_str = u_val[2:]
                    padding = len(b64_str) % 4
                    if padding:
                        b64_str += "=" * (4 - padding)
                    import base64
                    return base64.b64decode(b64_str).decode('utf-8', errors='ignore')
    except Exception:
        pass
    return url

def extract_google(html):
    results = []
    links = re.findall(r'<a[^>]*href="/url\?q=([^&"]+)[^>]*>(.*?)</a>', html, re.DOTALL)
    for url, text in links:
        clean_url = urllib.parse.unquote(url)
        if "google.com" not in clean_url and not clean_url.startswith("/"):
            results.append({
                "title": clean_text(text) if clean_text(text) else "Google Result",
                "url": clean_url
            })
    return results

def extract_bing(html):
    results = []
    h2_blocks = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    for block in h2_blocks:
        link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if link_match:
            href, title = link_match.groups()
            results.append({
                "title": clean_text(title),
                "url": decode_url(href)
            })
    return results

def extract_yahoo(html):
    results = []
    matches = re.findall(r'href="(https?://r\.search\.yahoo\.com/[^"]+)"[^>]*>(.*?)</a>', html)
    for href, title in matches:
        results.append({
            "title": clean_text(title),
            "url": decode_url(href)
        })
    return results

def extract_ddg(html):
    results = []
    matches = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
    for href, title in matches:
        results.append({
            "title": clean_text(title),
            "url": decode_url(href)
        })
    return results

def run_query(query):
    print(f"\n[Search] Query: '{query}'")
    engines = {
        "Google": (f"{get_base_url('google')}/search?q={urllib.parse.quote(query)}&num=10&gbv=1", extract_google),
        "Bing": (f"{get_base_url('bing')}/search?q={urllib.parse.quote(query)}", extract_bing),
        "Yahoo": (f"{get_base_url('yahoo')}/search?p={urllib.parse.quote(query)}", extract_yahoo),
        "DuckDuckGo": (f"{get_base_url('duckduckgo')}/html/?q={urllib.parse.quote(query)}", extract_ddg)
    }
    
    for engine_name, (url, extractor) in engines.items():
        req = urllib.request.Request(url)
        apply_bypass_headers(req, mode='pro')
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                html = response.read().decode('utf-8', errors='ignore')
                results = extractor(html)
                hits = 0
                for r in results:
                    url_lower = r["url"].lower()
                    if any(ind in url_lower for ind in TARGET_INDICATORS):
                        print(f"  [MATCH] [{engine_name}]: {r['title']} -> {r['url']}")
                        hits += 1
                if results and not hits:
                    print(f"  [INFO] [{engine_name}] Top result: {results[0]['title']} -> {results[0]['url']}")
                elif not results:
                    print(f"  [BLOCKED] [{engine_name}] No results parsed (WAF Blocked or Empty)")
        except Exception as e:
            print(f"  [ERROR] [{engine_name}] Error: {e}")
        time.sleep(random.uniform(0.5, 1.0))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        queries = [" ".join(sys.argv[1:])]
    else:
        queries = [
            "Chase Kinslow Monroe Police Department report 26-29572",
            "Chase Kinslow Affirm dispute archive",
            "Charles Kinslow CFPB complaint 260717-35668593"
        ]
        
    print("=== STARTING DIRECT SEARCH TRACKER (FIREPROX ENABLED) ===")
    for q in queries:
        run_query(q)
