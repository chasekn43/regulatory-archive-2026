import os
import sys
import time
import json
import random
import urllib.request
import urllib.parse
import re
from html import unescape
from datetime import datetime
from fireprox_config import get_base_url
from waf_bypass_headers import apply_bypass_headers

# Ensure UTF-8 output on Windows pwsh
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

NAME = "Chase Kinslow"

# Base repository keywords and identifiers
REPO_TOPICS = [
    "Fintech BNPL merchant dispute",
    "CFPB Administrative Procedures Act",
    "Customer service refund delays BNPL",
    "Point of sale lines of credit dispute",
    "Regulation Z billing error resolution",
    "CFPB complaint 260717-35668593",
    "Monroe Police Department report 26-29572",
    "Affirm Inc CFPB complaint",
    "Kinslow v Affirm public evidentiary record",
    "Morgan Lewis Bockius lawsuit Affirm",
    "Andy Chen Affirm cease and desist",
    "Scott Williams Affirm Vice President Client Success",
    "Perfume Empire tracking 1LSDCR10011QF38",
    "Louisiana AG Liz Murrill dispute submission",
    "California AG Rob Bonta dispute notice",
    "FTC fraud web affidavit Affirm",
    "Shop app unauthorized intrusion Affirm",
    "Affirm in-app payment lock BillPay workaround",
    "CFPB complaint rebuttal Affirm false response",
    "Madison Marshall Arjun Rao Morgan Lewis",
    "Kinslow Fintech Dispute Case Study"
]

TARGET_INDICATORS = [
    "kinslow-regulatory-archive.org",
    "chasekn43",
    "regulatory-archive-2026",
    "regulatory-archive.kinslow.co",
    "kinslow.co",
    "github.com/chasekn43",
    "260717-35668593",
    "26-29572",
    "kinslow-fintech-dispute"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

def clean_text(html_str):
    if not html_str:
        return ""
    cleanr = re.compile(r'<.*?>')
    cleantext = re.sub(cleanr, '', html_str)
    return unescape(cleantext).strip()

def build_query_variations(name, count=20):
    """Generates dynamically varied search query strings always incorporating the user's name."""
    modifiers = [
        "",
        "github",
        "public record",
        "evidence vault",
        "case study",
        "documents",
        "dispute",
        "legal notice"
    ]
    queries = []
    shuffled_topics = list(REPO_TOPICS)
    random.shuffle(shuffled_topics)
    
    for topic in shuffled_topics:
        mod = random.choice(modifiers)
        if mod:
            q = f"{name} {topic} {mod}".strip()
        else:
            q = f"{name} {topic}".strip()
        queries.append(q)
        
    return queries[:count]

# DuckDuckGo HTML parser
def fetch_duckduckgo(query):
    url = f"{get_base_url('duckduckgo')}/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://html.duckduckgo.com/"
    }
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<a class="result__url" href="(.*?)">(.*?)</a>.*?<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
            if not matches:
                simple = re.findall(r'<a class="result__url" href="(.*?)">(.*?)</a>', html)
                for h, t in simple:
                    results.append({"title": clean_text(t), "url": clean_text(h), "snippet": ""})
            else:
                for h, t, s in matches:
                    results.append({"title": clean_text(t), "url": clean_text(h), "snippet": clean_text(s)})
    except Exception as e:
        results.append({"error": str(e)})
    return results

# Bing Search parser
def fetch_bing(query):
    url = f"{get_base_url('bing')}/search?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            items = re.findall(r'<li class="b_algo">.*?<h2><a href="(http[s]?://[^"]+)"[^>]*>(.*?)</a></h2>', html, re.DOTALL)
            if not items:
                items = re.findall(r'<h2><a href="(http[s]?://[^"]+)"[^>]*>(.*?)</a></h2>', html)
            for h, t in items:
                results.append({"title": clean_text(t), "url": h, "snippet": ""})
    except Exception as e:
        results.append({"error": str(e)})
    return results

# Yahoo Search parser
def fetch_yahoo(query):
    url = f"{get_base_url('yahoo')}/search?p={urllib.parse.quote(query)}&nojs=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1"
    }
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<h3 class="title"[^>]*><a href="(https?://[^"]+)"[^>]*>(.*?)</a></h3>', html)
            if not matches:
                matches = re.findall(r'href="(https?://r\.search\.yahoo\.com/[^"]+)"[^>]*>(.*?)</a>', html)
            for h, t in matches:
                results.append({"title": clean_text(t), "url": h, "snippet": ""})
    except Exception as e:
        results.append({"error": str(e)})
    return results

# Google Search parser
def fetch_google(query):
    url = f"{get_base_url('google')}/search?q={urllib.parse.quote(query)}&num=15"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            raw_links = re.findall(r'href="/url\?q=(http[s]?://[^&]+)&amp;', html)
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html)
            if not raw_links:
                # Modern desktop layout matches
                raw_links = re.findall(r'<a href="(https?://[^"]+)" data-ved=', html)
            for i, l in enumerate(raw_links):
                if "google.com" not in l and "youtube.com" not in l:
                    t = clean_text(titles[i]) if i < len(titles) else "Google Search Result"
                    results.append({"title": t, "url": urllib.parse.unquote(l), "snippet": ""})
    except Exception as e:
        results.append({"error": str(e)})
    return results

def check_target_match(url, title, snippet):
    combined = (str(url) + " " + str(title) + " " + str(snippet)).lower()
    for ind in TARGET_INDICATORS:
        if ind.lower() in combined:
            return True, ind
    return False, None

def run_continuous_audit(passes=3, queries_per_pass=6):
    print(f"\n========================================================================", flush=True)
    print(f"  STARTING MULTI-ENGINE CONTINUOUS SEARCH AUDIT", flush=True)
    print(f"  Target Person: '{NAME}'", flush=True)
    print(f"  Target Repository Indicators: {TARGET_INDICATORS[:4]}...", flush=True)
    print(f"  Engines: DuckDuckGo, Bing, Yahoo, Google", flush=True)
    print(f"========================================================================\n", flush=True)
    
    audit_history = []
    total_hits_count = 0
    log_file = "continuous_search_audit_results.json"

    for pass_num in range(1, passes + 1):
        pass_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        queries = build_query_variations(NAME, count=queries_per_pass)
        
        print(f"\n--- PASS #{pass_num}/{passes} @ {pass_time} ---", flush=True)
        print(f"Generated {len(queries)} dynamic keyword variations including name '{NAME}':", flush=True)
        for idx, q in enumerate(queries, 1):
            print(f"  {idx}. \"{q}\"", flush=True)
        print("------------------------------------------------------------------------", flush=True)
        
        pass_data = {
            "pass_number": pass_num,
            "timestamp": pass_time,
            "queries": []
        }
        
        for q_idx, query in enumerate(queries, 1):
            print(f"\n[{pass_num}.{q_idx}] Querying engines for: '{query}'", flush=True)
            query_record = {
                "query": query,
                "engines": {},
                "hits": []
            }
            
            # 1. DuckDuckGo
            ddg = fetch_duckduckgo(query)
            query_record["engines"]["DuckDuckGo"] = ddg
            
            # 2. Bing
            bing = fetch_bing(query)
            query_record["engines"]["Bing"] = bing
            
            # 3. Yahoo
            yahoo = fetch_yahoo(query)
            query_record["engines"]["Yahoo"] = yahoo
            
            # 4. Google
            google = fetch_google(query)
            query_record["engines"]["Google"] = google
            
            # Check target hits
            matches = []
            for eng_name, res_list in query_record["engines"].items():
                for item in res_list:
                    if isinstance(item, dict) and "url" in item:
                        matched, ind = check_target_match(item.get("url", ""), item.get("title", ""), item.get("snippet", ""))
                        if matched:
                            matches.append({
                                "engine": eng_name,
                                "indicator": ind,
                                "title": item.get("title"),
                                "url": item.get("url")
                            })
            
            query_record["hits"] = matches
            if matches:
                total_hits_count += len(matches)
                print(f"   🎯 MATCH DETECTED! {len(matches)} hit(s) found for '{query}' across engines:", flush=True)
                for m in matches:
                    print(f"      • [{m['engine']}] ({m['indicator']}) {m['title']} -> {m['url']}", flush=True)
            else:
                print(f"   ✓ Searched DDG ({len(ddg)}), Bing ({len(bing)}), Yahoo ({len(yahoo)}), Google ({len(google)}) - No hits in top results", flush=True)
            
            pass_data["queries"].append(query_record)
            time.sleep(1) # brief pause between queries
            
        audit_history.append(pass_data)

        # Incrementally save results to disk after each pass
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(audit_history, f, indent=2)

        if pass_num < passes:
            print(f"\nPass #{pass_num} complete. Pausing before next varied keyword pass...", flush=True)
            time.sleep(2)
            
    print(f"\n========================================================================", flush=True)
    print(f"  AUDIT COMPLETE: Ran {passes} passes, queried {passes * queries_per_pass} total search variations.", flush=True)
    print(f"  Total Target Indexing Hits Detected: {total_hits_count}", flush=True)
    print(f"  Detailed log saved to: {os.path.abspath(log_file)}", flush=True)
    print(f"========================================================================\n", flush=True)
    return audit_history

if __name__ == "__main__":
    passes_to_run = 3
    if len(sys.argv) > 1:
        try:
            passes_to_run = int(sys.argv[1])
        except ValueError:
            pass
    run_continuous_audit(passes=passes_to_run, queries_per_pass=5)
