import urllib.parse
import urllib.request
import re
import json
import random
import sys
import os
import subprocess
import time
from html import unescape
from datetime import datetime
import socket
from fireprox_config import get_base_url
from waf_bypass_headers import apply_bypass_headers
import threading

socket.setdefaulttimeout(3)
browser_lock = threading.Lock()

# Ensure stdout handles utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load search keywords from keywords.txt or fallback to defaults
default_queries = [
    "Chase Kinslow Fintech BNPL merchant dispute",
    "Charles W. Kinslow IV CFPB Administrative Procedures Act",
    "Chase Kinslow customer service refund delays",
    "Charles W. Kinslow IV point of sale lines of credit",
    "Chase Kinslow Buy Now Pay Later loan dispute",
    "Charles W. Kinslow IV Regulation Z billing error",
    "Chase Kinslow Kinslow v Affirm",
    "Charles W. Kinslow IV Kinslow v Affirm"
]

keywords_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords.txt")
if os.path.exists(keywords_file):
    try:
        with open(keywords_file, "r", encoding="utf-8") as kf:
            queries = [line.strip() for line in kf if line.strip() and not line.strip().startswith("#")]
        # Deduplicate while preserving order
        queries = list(dict.fromkeys(queries))
        print(f"[Config] Loaded {len(queries)} unique queries from keywords.txt")
    except Exception as e:
        print(f"[Config] Error loading keywords.txt: {e}. Using defaults.")
        queries = default_queries
else:
    try:
        with open(keywords_file, "w", encoding="utf-8") as kf:
            kf.write("# GRC Keywords list. Add one keyword per line to track in search results.\n")
            for q in default_queries:
                kf.write(f"{q}\n")
        print(f"[Config] Generated default keywords.txt at: {keywords_file}")
    except Exception as e:
        pass
    queries = default_queries

TARGET_INDICATORS = [
    "kinslow-regulatory-archive.org",
    "chasekn43",
    "regulatory-archive-2026",
    "regulatory-archive.kinslow.co",
    "kinslow.co",
    "kinslow"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]

import threading
from concurrent.futures import ThreadPoolExecutor

USE_PROXY = True
verified_lock = threading.Lock()
verified_pools = {
    "Google": set(),
    "Bing": set(),
    "Yahoo": set(),
    "DuckDuckGo": set()
}

raw_proxies_cache = []
last_fetch_time = 0
cache_lock = threading.Lock()

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def get_raw_proxies():
    global last_fetch_time, raw_proxies_cache
    now = time.time()
    with cache_lock:
        if now - last_fetch_time < 90 and raw_proxies_cache:
            return raw_proxies_cache

    proxy_urls = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=yes&anonymity=anonymous",
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=yes&anonymity=elite",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    ]
    raw_list = []
    for url in proxy_urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': random.choice(USER_AGENTS)})
            with urllib.request.urlopen(req, timeout=8) as response:
                content = response.read().decode('utf-8', errors='ignore')
                found = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}\b', content)
                raw_list.extend(found)
        except Exception:
            pass
            
    with cache_lock:
        if raw_list:
            raw_proxies_cache = list(set(raw_list))
            last_fetch_time = now
        return raw_proxies_cache

def test_single_proxy(proxy):
    timeout = 1.5
    tests = [
        {"name": "Google", "url": f"{get_base_url('google')}/search?q=test&gbv=1"},
        {"name": "Bing", "url": f"{get_base_url('bing')}/search?q=test"},
        {"name": "Yahoo", "url": f"{get_base_url('yahoo')}/search?p=test"},
        {"name": "DuckDuckGo", "url": f"{get_base_url('duckduckgo')}/html/?q=test"}
    ]
    random.shuffle(tests)
    for test in tests:
        name = test["name"]
        test_url = test["url"]
        try:
            proxy_support = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_support, NoRedirectHandler())
            req = urllib.request.Request(test_url, headers={'User-Agent': random.choice(USER_AGENTS)})
            with opener.open(req, timeout=timeout) as resp:
                if resp.status == 200:
                    with verified_lock:
                        verified_pools[name].add(proxy)
        except Exception:
            # If the proxy connection fails, it is dead. Stop checking other engines.
            break

def run_validator():
    print("Initiating fast parallel proxy validator...")
    raw_proxies = get_raw_proxies()
    if raw_proxies:
        local_list = list(raw_proxies)
        random.shuffle(local_list)
        # Limit validation to first 250 proxies for speed
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(test_single_proxy, local_list[:250])
    with verified_lock:
        counts = {name: len(pool) for name, pool in verified_pools.items()}
        print(f"Proxy pools populated: {counts}")


def clean_text(html_str):
    cleanr = re.compile(r'<.*?>')
    cleantext = re.sub(cleanr, '', html_str)
    return unescape(cleantext).strip()

def decode_redirect_url(url):
    try:
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
                    # Strip the first 2 characters prefix (e.g. 'a1')
                    b64_str = u_val[2:]
                    # Add base64 padding if required
                    padding = len(b64_str) % 4
                    if padding:
                        b64_str += "=" * (4 - padding)
                    try:
                        import base64
                        decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                        if decoded.startswith("http"):
                            return decoded
                    except Exception:
                        pass
    except Exception:
        pass
    return url


def fetch_with_metrics(url, extractor, engine_name=None):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    if "duckduckgo.com" in url:
        headers["Referer"] = f"{get_base_url('duckduckgo')}/"
    elif "bing.com" in url:
        headers["Referer"] = f"{get_base_url('bing')}/"
    elif "google.com" in url:
        headers["Referer"] = f"{get_base_url('google')}/"
    elif "yahoo.com" in url:
        headers["Referer"] = f"{get_base_url('yahoo')}/"
        
    start_time = time.time()
    results = []
    error = None
    status_code = 200
    
    use_proxy = USE_PROXY and engine_name in verified_pools
    success = False
    
    if use_proxy:
        with verified_lock:
            pool = list(verified_pools[engine_name])
        
        if pool:
            random.shuffle(pool)
            for proxy in pool[:8]:
                try:
                    proxy_support = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
                    opener = urllib.request.build_opener(proxy_support)
                    req = urllib.request.Request(url, headers=headers)
                    apply_bypass_headers(req, mode='pro')
                    with opener.open(req, timeout=1.5) as response:
                        status_code = response.getcode()
                        html = response.read().decode('utf-8', errors='ignore')
                        results = extractor(html)
                        if len(results) > 0 or "did not match any documents" in html.lower() or "no results found" in html.lower():
                            success = True
                            break
                except Exception:
                    pass
                    
    if not success:
        if use_proxy:
            print(f"No validated proxies succeeded for {engine_name}. Falling back to direct connection...")
        req = urllib.request.Request(url, headers=headers)
        apply_bypass_headers(req, mode='pro')
        try:
            with urllib.request.urlopen(req, timeout=1.5) as response:
                status_code = response.getcode()
                html = response.read().decode('utf-8', errors='ignore')
                results = extractor(html)
                success = True
        except Exception as e:
            error = str(e)
            status_code = getattr(e, 'code', 500) if hasattr(e, 'code') else 500
            
        if not success:
            # Obscura stealth fetch fallback is disabled to prevent non-interactive service hangs on Windows
            pass

    elapsed_ms = round((time.time() - start_time) * 1000, 2)


    
    # Check target hits
    hits = 0
    hit_details = []
    for r in results:
        combined = f"{r.get('title', '')} {r.get('url', '')} {r.get('snippet', '')}".lower()
        matched = [ind for ind in TARGET_INDICATORS if ind in combined]
        if matched:
            hits += 1
            hit_details.append({"title": r.get("title"), "url": r.get("url"), "matched_indicators": matched})

    return {
        "response_time_ms": elapsed_ms,
        "status_code": status_code,
        "results_count": len(results),
        "target_hits": hits,
        "hit_details": hit_details,
        "error": error,
        "raw_results": results,
        "html": html if 'html' in locals() else ""
    }

def extract_duckduckgo(html):
    results = []
    # DuckDuckGo HTML results titles are inside: <a class="result__a" href="...">
    matches = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
    if not matches:
        matches = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        
    snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
    for i, (l_href, l_title) in enumerate(matches):
        snip = clean_text(snippets[i]) if i < len(snippets) else ""
        results.append({
            "title": clean_text(l_title), 
            "url": decode_redirect_url(clean_text(l_href)), 
            "snippet": snip
        })
    return results

ddg_captcha_failures = 0
google_captcha_failures = 0

def search_duckduckgo(query):
    global ddg_captcha_failures
    url = f"{get_base_url('duckduckgo')}/html/?q={urllib.parse.quote(query)}"
    res = fetch_with_metrics(url, extract_duckduckgo, "DuckDuckGo")
    
    # Check if direct request was blocked or timed out
    is_blocked = (
        res.get("status_code", 200) in [403, 429, 503] or
        "bots use duckduckgo" in (res.get("error") or "").lower() or
        res.get("results_count", 0) == 0
    )
    
    if is_blocked:
        if ddg_captcha_failures >= 3:
            # Skip browser fallback to save time since the current IP is blocked
            return res
            
        print(f"    [DuckDuckGo Blocked/Empty] Triggering ddg_bypass_searcher solver for: '{query}'...")
        start_time = time.time()
        try:
            import threading
            thread_name = threading.current_thread().name
            match = re.search(r'_(\d+)$', thread_name)
            worker_id = str(int(match.group(1)) % 3) if match else "0"
            
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddg_bypass_searcher.py")
            cmd = [sys.executable, script_path, worker_id, query]
            with browser_lock:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            
            if result.returncode == 0 and result.stdout.strip():
                html = result.stdout
                results = extract_duckduckgo(html)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                
                # Check target hits
                hits = 0
                hit_details = []
                for r in results:
                    combined = f"{r.get('title', '')} {r.get('url', '')} {r.get('snippet', '')}".lower()
                    matched = [ind for ind in TARGET_INDICATORS if ind in combined]
                    if matched:
                        hits += 1
                        hit_details.append({"title": r.get("title"), "url": r.get("url"), "matched_indicators": matched})
                
                print(f"    [DDG Bypass Success] Found {len(results)} results, {hits} target hits via browser automation.")
                return {
                    "response_time_ms": elapsed_ms,
                    "status_code": 200,
                    "results_count": len(results),
                    "target_hits": hits,
                    "hit_details": hit_details,
                    "error": None,
                    "raw_results": results
                }
            elif result.returncode == 2:
                print("    [DDG Bypass Blocked] CAPTCHA detected in browser. Clean IP/VPN required.")
                ddg_captcha_failures += 1
                return {
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "status_code": 403,
                    "results_count": 0,
                    "target_hits": 0,
                    "hit_details": [],
                    "error": "Bypass failed: CAPTCHA block in browser (clean IP/VPN required)",
                    "raw_results": []
                }
            else:
                err_msg = result.stderr.strip() if result.stderr else "Empty solver output"
                print(f"    [DDG Bypass Failed] Solver error: {err_msg}")
                return {
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "status_code": 503,
                    "results_count": 0,
                    "target_hits": 0,
                    "hit_details": [],
                    "error": f"Bypass failed: {err_msg}",
                    "raw_results": []
                }
        except Exception as e:
            print(f"    [DDG Bypass Exception] Error running solver: {e}")
            return {
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "status_code": 500,
                "results_count": 0,
                "target_hits": 0,
                "hit_details": [],
                "error": f"Bypass exception: {str(e)}",
                "raw_results": []
            }
            
    return res

def extract_google(html):
    results = []
    # Google basic HTML search results links are /url?q=...
    links = re.findall(r'<a[^>]*href="/url\?q=([^&"]+)[^>]*>(.*?)</a>', html, re.DOTALL)
    for url, text in links:
        clean_url = urllib.parse.unquote(url)
        if "google.com" not in clean_url and not clean_url.startswith("/"):
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            results.append({
                "title": clean_text if clean_text else "Google Result", 
                "url": clean_url, 
                "snippet": ""
            })
    return results

def search_google(query):
    global google_captcha_failures
    # Try FireProx proxied search first
    url = f"{get_base_url('google')}/search?q={urllib.parse.quote(query)}&num=10&gbv=1"
    res = fetch_with_metrics(url, extract_google, "Google")
    
    # Check if direct search was blocked
    is_blocked = (
        res.get("status_code", 200) in [403, 429, 503] or
        "google.com/sorry" in (res.get("error") or "") or
        "google.com/sorry" in res.get("html", "") or
        "recaptcha" in res.get("html", "")
    )
    
    if is_blocked:
        if google_captcha_failures >= 3:
            # Skip solver to save time since the current IP/connection is blocked
            return res
            
        print(f"    [Google Blocked/Empty] Triggering GoogleRecaptchaBypass solver for: '{query}'...")
        start_time = time.time()
        try:
            # Parse worker ID from thread name
            import threading
            thread_name = threading.current_thread().name
            match = re.search(r'_(\d+)$', thread_name)
            worker_id = str(int(match.group(1)) % 3) if match else "0"
            
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_bypass_searcher.py")
            cmd = [sys.executable, script_path, worker_id, query]
            with browser_lock:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            
            if result.returncode == 0 and result.stdout.strip():
                html = result.stdout
                results = extract_google(html)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                
                # Check target hits
                hits = 0
                hit_details = []
                for r in results:
                    combined = f"{r.get('title', '')} {r.get('url', '')} {r.get('snippet', '')}".lower()
                    matched = [ind for ind in TARGET_INDICATORS if ind in combined]
                    if matched:
                        hits += 1
                        hit_details.append({"title": r.get("title"), "url": r.get("url"), "matched_indicators": matched})
                
                print(f"    [Bypass Success] Found {len(results)} results, {hits} target hits via GoogleRecaptchaBypass.")
                return {
                    "response_time_ms": elapsed_ms,
                    "status_code": 200,
                    "results_count": len(results),
                    "target_hits": hits,
                    "hit_details": hit_details,
                    "error": None,
                    "raw_results": results
                }
            else:
                err_msg = result.stderr.strip() if result.stderr else "Empty solver output"
                print(f"    [Bypass Failed] Solver error: {err_msg}")
                google_captcha_failures += 1
                return {
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "status_code": 503,
                    "results_count": 0,
                    "target_hits": 0,
                    "hit_details": [],
                    "error": f"Bypass failed: {err_msg}",
                    "raw_results": []
                }
        except Exception as e:
            print(f"    [Bypass Exception] Error running solver: {e}")
            google_captcha_failures += 1
            return {
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "status_code": 500,
                "results_count": 0,
                "target_hits": 0,
                "hit_details": [],
                "error": f"Bypass exception: {str(e)}",
                "raw_results": []
            }
            
    return res

def extract_bing(html):
    results = []
    # Find all h2 blocks which contain result links
    h2_blocks = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    for block in h2_blocks:
        link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if link_match:
            href, title = link_match.groups()
            
            # Filter out internal pages but keep search result redirect URLs containing '/ck/a'
            is_internal = False
            if "bing.com" in href:
                if "/ck/a" not in href:
                    is_internal = True
            elif "microsoft.com" in href or "live.com" in href:
                is_internal = True
                
            if not is_internal:
                results.append({
                    "title": clean_text(title), 
                    "url": decode_redirect_url(href), 
                    "snippet": ""
                })
    return results

def search_bing(query):
    url = f"{get_base_url('bing')}/search?q={urllib.parse.quote(query)}"
    return fetch_with_metrics(url, extract_bing, "Bing")

def extract_yahoo(html):
    results = []
    matches = re.findall(r'<h3 class="title"[^>]*><a href="(https?://r\.search\.yahoo\.com/[^"]+)"[^>]*>(.*?)</a></h3>', html)
    if not matches:
        matches = re.findall(r'href="(https?://r\.search\.yahoo\.com/[^"]+)"[^>]*>(.*?)</a>', html)
    for href, title in matches:
        results.append({"title": clean_text(title), "url": decode_redirect_url(href), "snippet": ""})
    return results

def search_yahoo(query):
    url = f"{get_base_url('yahoo')}/search?p={urllib.parse.quote(query)}"
    return fetch_with_metrics(url, extract_yahoo, "Yahoo")

# Multi-key rotation database for Exa
EXA_KEYS = [
    "47fee989-446a-44be-8aa0-733c1a688361",
    "5365e676-b3a1-4dea-a0fb-140c817c0bcc",
    "bd320fa0-9814-41f2-b107-ae1e38474eec",
    "7cf81a94-d8cf-4e6f-9089-1ac2242bee15"
]
exa_key_index = 0

def search_exa(query):
    global exa_key_index
    url = "https://api.exa.ai/search"
    payload = {
        "query": query,
        "useAutoprompt": False,
        "numResults": 10
    }
    
    start_time = time.time()
    results = []
    error = None
    status_code = 200
    
    # Try up to len(EXA_KEYS) times
    for attempt in range(len(EXA_KEYS)):
        current_key = EXA_KEYS[exa_key_index]
        headers = {
            "x-api-key": current_key,
            "Content-Type": "application/json"
        }
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers, 
                method='POST'
            )
            apply_bypass_headers(req, mode='pro')
            with urllib.request.urlopen(req, timeout=10) as response:
                status_code = response.getcode()
                res_data = json.loads(response.read().decode('utf-8'))
                for r in res_data.get("results", []):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("text", "")
                    })
                # Success - break out of attempts loop
                break
        except Exception as e:
            error = str(e)
            is_limit = "402" in error or "429" in error
            if is_limit:
                print(f"    [Exa Key Failed] Key index {exa_key_index} returned status ({error}). Rotating to next key...")
                exa_key_index = (exa_key_index + 1) % len(EXA_KEYS)
                # Continue loop to try next key
                continue
            else:
                status_code = 500
                break
        
    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    
    # Check target hits
    hits = 0
    hit_details = []
    for r in results:
        combined = f"{r.get('title', '')} {r.get('url', '')} {r.get('snippet', '')}".lower()
        matched = [ind for ind in TARGET_INDICATORS if ind in combined]
        if matched:
            hits += 1
            hit_details.append({"title": r.get("title"), "url": r.get("url"), "matched_indicators": matched})
            
    return {
        "response_time_ms": elapsed_ms,
        "status_code": status_code,
        "results_count": len(results),
        "target_hits": hits,
        "hit_details": hit_details,
        "error": error,
    }

# Multi-key rotation database
TAVILY_KEYS = [
    "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",
    "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",
    "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",
    "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"
]
tavily_key_index = 0

def search_tavily(query):
    global tavily_key_index
    url = "https://api.tavily.com/search"
    
    # Try all keys in rotation if one fails
    for attempt in range(len(TAVILY_KEYS)):
        current_key = TAVILY_KEYS[tavily_key_index]
        payload = {
            "api_key": current_key,
            "query": query,
            "search_depth": "basic"
        }
        headers = {"Content-Type": "application/json"}
        start_time = time.time()
        results = []
        error = None
        status_code = 200
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers, 
                method='POST'
            )
            apply_bypass_headers(req, mode='pro')
            with urllib.request.urlopen(req, timeout=10) as response:
                status_code = response.getcode()
                res_data = json.loads(response.read().decode('utf-8'))
                for r in res_data.get("results", []):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", "")
                    })
        except Exception as e:
            error = str(e)
            if hasattr(e, 'code'):
                status_code = e.code
            else:
                status_code = 500
                
        # If this key succeeded (status 200 and has results), return the results!
        if status_code == 200 and not error and results:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            hits = 0
            hit_details = []
            for r in results:
                combined = f"{r.get('title', '')} {r.get('url', '')} {r.get('snippet', '')}".lower()
                matched = [ind for ind in TARGET_INDICATORS if ind in combined]
                if matched:
                    hits += 1
                    hit_details.append({"title": r.get("title"), "url": r.get("url"), "matched_indicators": matched})
            return {
                "response_time_ms": elapsed_ms,
                "status_code": status_code,
                "results_count": len(results),
                "target_hits": hits,
                "hit_details": hit_details,
                "error": None,
                "raw_results": results
            }
        
        # If we got a credit limit (432) or rate limit (429) error, rotate to the next key!
        print(f"    [Tavily Key Failed] Key index {tavily_key_index} returned status {status_code} ({error}). Rotating to next key...")
        tavily_key_index = (tavily_key_index + 1) % len(TAVILY_KEYS)
        
    # If all keys failed, fall back to Exa Search API proxy!
    print("    [All Tavily Keys Failed] Falling back to Exa Search API proxy...")
    return search_exa(query)

all_results = {}
engine_stats = {
    "Google": {"queries": 0, "total_time_ms": 0, "total_results": 0, "total_hits": 0, "errors": 0},
    "Bing": {"queries": 0, "total_time_ms": 0, "total_results": 0, "total_hits": 0, "errors": 0},
    "Yahoo": {"queries": 0, "total_time_ms": 0, "total_results": 0, "total_hits": 0, "errors": 0},
    "DuckDuckGo": {"queries": 0, "total_time_ms": 0, "total_results": 0, "total_hits": 0, "errors": 0},
    "Tavily": {"queries": 0, "total_time_ms": 0, "total_results": 0, "total_hits": 0, "errors": 0},
    "Exa": {"queries": 0, "total_time_ms": 0, "total_results": 0, "total_hits": 0, "errors": 0}
}

def execute_single_query(q):
    print(f"Running sweep for query: '{q}'")
    q_res = {}
    for engine_name, search_fn in [
        ("Google", search_google),
        ("Bing", search_bing),
        ("Yahoo", search_yahoo),
        ("DuckDuckGo", search_duckduckgo)
    ]:
        try:
            q_res[engine_name] = search_fn(q)
        except Exception as e:
            q_res[engine_name] = {
                "response_time_ms": 0,
                "status_code": 500,
                "results_count": 0,
                "target_hits": 0,
                "hit_details": [],
                "error": str(e),
                "raw_results": []
            }
        # Small delay inside worker to spread out queries
        if engine_name in ["Google", "Bing", "Yahoo", "DuckDuckGo"]:
            time.sleep(random.uniform(0.5, 1.5))
    return q, q_res

print(f"Starting Multi-Engine Keyword Verification Sweep in Parallel at {datetime.now().isoformat()}...")
run_validator() # Pre-populate active proxies

# Run queries concurrently using ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=3) as executor:
    results_map = executor.map(execute_single_query, queries)
    for q, q_res in results_map:
        all_results[q] = q_res
        for engine, res in q_res.items():
            engine_stats[engine]["queries"] += 1
            engine_stats[engine]["total_time_ms"] += res.get("response_time_ms", 0)
            engine_stats[engine]["total_results"] += res.get("results_count", 0)
            engine_stats[engine]["total_hits"] += res.get("target_hits", 0)
            if res.get("error"):
                engine_stats[engine]["errors"] += 1

output_data = {
    "timestamp": datetime.now().isoformat(),
    "queries_executed": len(queries),
    "engine_summary": engine_stats,
    "detailed_results": all_results
}

with open("query_verification_run.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print("\n--- SWEEP SUMMARY METRICS ---")
for engine, stats in engine_stats.items():
    avg_time = round(stats["total_time_ms"] / stats["queries"], 2) if stats["queries"] > 0 else 0
    hit_rate = round((stats["total_hits"] / stats["queries"]) * 100, 2) if stats["queries"] > 0 else 0
    print(f"Engine: {engine:<12} | Avg Latency: {avg_time:>7.1f}ms | Total Results: {stats['total_results']:>3} | Target Hits: {stats['total_hits']:>3} | Hit Rate per Query: {hit_rate:>5.1f}% | Errors: {stats['errors']}")

print("\nSearch verification sweep complete. Saved to query_verification_run.json.")

