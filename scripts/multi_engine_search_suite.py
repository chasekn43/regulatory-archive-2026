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

# Ensure stdout uses utf-8 encoding on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Define target domain & handle indicators
TARGET_INDICATORS = [
    "kinslow-regulatory-archive.org",
    "chasekn43",
    "regulatory-archive-2026",
    "regulatory-archive.kinslow.co",
    "kinslow.co",
    "github.com/chasekn43",
    "260717-35668593",
    "26-29572",
    "chase kinslow",
    "charles w. kinslow"
]

# Primary user name
NAME = "Chase Kinslow"

# Comprehensive keyword templates combining user name with GitHub repository topics
KEYWORD_TEMPLATES = [
    "{name} Fintech BNPL merchant dispute",
    "{name} CFPB Administrative Procedures Act",
    "{name} customer service refund delays BNPL",
    "{name} point of sale lines of credit dispute",
    "{name} Affirm CFPB complaint 260717-35668593",
    "{name} Kinslow v Affirm public evidentiary record",
    "{name} Affirm Morgan Lewis Bockius lawsuit",
    "{name} Andy Chen Affirm cease and desist",
    "{name} Monroe Police Department incident report 26-29572",
    "{name} Perfume Empire tracking 1LSDCR10011QF38",
    "{name} Louisiana AG Liz Murrill dispute submission",
    "{name} California AG Rob Bonta dispute notice",
    "{name} FTC fraud web affidavit Affirm",
    "{name} Shop app unauthorized intrusion Affirm",
    "{name} Regulation Z billing error resolution",
    "{name} Madison Marshall Arjun Rao Morgan Lewis",
    "{name} Scott Williams Affirm Vice President Client Success",
    "{name} Affirm in-app payment lock BillPay workaround",
    "{name} CFPB complaint rebuttal Affirm false response"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

def clean_text(html_str):
    cleanr = re.compile(r'<.*?>')
    cleantext = re.sub(cleanr, '', html_str)
    return unescape(cleantext).strip()

def decode_redirect_url(url):
    try:
        url = unescape(url)
        if "uddg=" in url:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if "uddg" in parsed:
                return parsed["uddg"][0]
        if "bing.com/ck/a?" in url and "&u=" in url:
            match = re.search(r'[?&]u=a1([A-Za-z0-9_-]+)', url)
            if match:
                b64 = match.group(1)
                b64 += '=' * (-len(b64) % 4)
                return base64.b64decode(b64.replace('-', '+').replace('_', '/')).decode('utf-8', errors='ignore')
        if "r.search.yahoo.com" in url and "/RU=" in url:
            match = re.search(r'/RU=([^/]+)/', url)
            if match:
                return urllib.parse.unquote(match.group(1))
    except Exception:
        pass
    return url

def search_duckduckgo(query):
    url = "https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    req = urllib.request.Request(url, data=data, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode('utf-8', errors='ignore')
            links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html)
            for href, title_html in links:
                if href.startswith("http") and "duckduckgo.com" not in href:
                    t_text = clean_text(title_html)
                    results.append({"title": t_text, "url": href, "snippet": ""})
    except Exception as e:
        results.append({"error": str(e)})
    return results

def search_google(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "en-US,en;q=0.9"}
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode('utf-8', errors='ignore')
            items = re.findall(r'class="result__a" href="([^"]+)">(.*?)</a>', html, re.DOTALL)
            for href, title_html in items:
                clean_u = decode_redirect_url(href)
                t_text = clean_text(title_html)
                if clean_u.startswith("http"):
                    results.append({"title": t_text, "url": clean_u, "snippet": ""})
    except Exception as e:
        results.append({"error": str(e)})
    return results

def search_bing(query):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": "SRCHHPGUSR=SRCHLANG=v-en"
    }
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            h = response.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.DOTALL)
            for href, title_html in matches:
                clean_u = decode_redirect_url(href)
                t_text = clean_text(title_html)
                if clean_u.startswith("http") and "bing.com" not in clean_u and "microsoft.com" not in clean_u and len(t_text) > 3:
                    results.append({"title": t_text, "url": clean_u, "snippet": ""})
    except Exception as e:
        results.append({"error": str(e)})
    return results

def search_yahoo(query):
    url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
    headers = {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "en-US,en;q=0.9"}
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<a[^>]+href="([^"]*r\.search\.yahoo\.com/[^"]*)"[^>]*>(.*?)</a>', html)
            for href, title in matches:
                ru = re.search(r'/RU=([^/]+)/', href)
                decoded = urllib.parse.unquote(ru.group(1)) if ru else href
                if "yahoo.com" not in decoded and decoded.startswith("http"):
                    results.append({"title": clean_text(title), "url": decoded, "snippet": ""})
    except Exception as e:
        results.append({"error": str(e)})
    return results

def is_target_match(url, title, snippet):
    combined = (url + " " + title + " " + snippet).lower()
    for ind in TARGET_INDICATORS:
        if ind.lower() in combined:
            return True, ind
    return False, None

def run_custom_queries(query_list, output_filename="batch_a_results.json"):
    print(f"\n=======================================================")
    print(f"  RUNNING EXPLICIT QUERY BATCH ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"  Queries count: {len(query_list)}")
    print(f"  Output file: {output_filename}")
    print(f"=======================================================\n")
    
    batch_results = {
        "timestamp": datetime.now().isoformat(),
        "query_set": query_list,
        "queries_run": []
    }
    
    for q_idx, q in enumerate(query_list, 1):
        print(f"[{q_idx}/{len(query_list)}] Querying 4 engines for: '{q}'")
        q_data = {
            "query": q,
            "engines": {}
        }
        
        # 1. DuckDuckGo
        ddg_res = search_duckduckgo(q)
        q_data["engines"]["DuckDuckGo"] = ddg_res
        
        # 2. Google
        g_res = search_google(q)
        q_data["engines"]["Google"] = g_res
        
        # 3. Bing
        b_res = search_bing(q)
        q_data["engines"]["Bing"] = b_res
        
        # 4. Yahoo
        y_res = search_yahoo(q)
        q_data["engines"]["Yahoo"] = y_res
        
        matches_found = []
        for eng_name, items in q_data["engines"].items():
            for item in items:
                if "url" in item:
                    matched, ind = is_target_match(item.get("url", ""), item.get("title", ""), item.get("snippet", ""))
                    if matched:
                        matches_found.append({"engine": eng_name, "indicator": ind, "title": item.get("title"), "url": item.get("url")})
        
        q_data["target_matches"] = matches_found
        ddg_count = len([it for it in ddg_res if 'url' in it])
        g_count = len([it for it in g_res if 'url' in it])
        b_count = len([it for it in b_res if 'url' in it])
        y_count = len([it for it in y_res if 'url' in it])
        print(f"   Done: DDG ({ddg_count}), Google ({g_count}), Bing ({b_count}), Yahoo ({y_count}). Matches: {len(matches_found)}")
        
        batch_results["queries_run"].append(q_data)
        time.sleep(1.5)
        
    out_path = os.path.join(os.path.dirname(__file__), output_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(batch_results, f, indent=2)
        
    print(f"\nExecution complete. Saved {len(query_list)} query findings to: {out_path}")
    return batch_results

from generate_200_queries import build_200_archive_queries

def run_search_pass(iteration_num, max_queries=10):
    domain = "kinslow-regulatory-archive.org"
    
    # Load 100% comprehensive archive queries (200 distinct queries across all sections)
    queries = build_200_archive_queries()

    random.shuffle(queries)
    selected_queries = queries[:min(max_queries, len(queries))]

    print(f"\n=======================================================")
    print(f"  RUNNING ARCHIVE 200-QUERY SEARCH PASS #{iteration_num} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"  Target Canonical Domain: {domain}")
    print(f"  Selected {len(selected_queries)} organic queries from the 200-query archive matrix")
    print(f"=======================================================\n")

    pass_results = {
        "timestamp": datetime.now().isoformat(),
        "pass_number": iteration_num,
        "canonical_domain": domain,
        "queries_run": []
    }

    for q_idx, q in enumerate(selected_queries, 1):
        print(f"[{q_idx}/{len(selected_queries)}] Running Connected Query: '{q}'")
        q_data = {
            "query": q,
            "engines": {}
        }

        # Run across engines
        ddg_res = search_duckduckgo(q)
        q_data["engines"]["DuckDuckGo"] = ddg_res

        g_res = search_google(q)
        q_data["engines"]["Google"] = g_res

        try:
            use_api = CONFIG.get('use_search_api') and CONFIG.get('bing_api_key')
        except NameError:
            use_api = False

        if use_api:
            b_res = search_bing_api(q)
        else:
            b_res = search_bing(q)
        q_data["engines"]["Bing"] = b_res

        y_res = search_yahoo(q)
        q_data["engines"]["Yahoo"] = y_res

        # Check target visibility
        matches_found = []
        for eng_name, items in q_data["engines"].items():
            for item in items:
                if "url" in item:
                    matched, ind = is_target_match(item.get("url", ""), item.get("title", ""), item.get("snippet", ""))
                    if matched:
                        matches_found.append({"engine": eng_name, "indicator": ind, "title": item.get("title"), "url": item.get("url")})

        q_data["target_matches"] = matches_found
        if matches_found:
            print(f"   >>> TARGET MATCH CONFIRMED! {len(matches_found)} links to kinslow-regulatory-archive.org / author found:")
            for m in matches_found[:4]:
                print(f"       [{m['engine']}] Found ({m['indicator']}): {m['url']}")
        else:
            engine_counts = [f"{eng} ({len([i for i in items if 'url' in i])})" for eng, items in q_data["engines"].items()]
            print(f"   Completed across {', '.join(engine_counts)}")

        pass_results["queries_run"].append(q_data)
        time.sleep(1.5)

    return pass_results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Engine Search Suite")
    parser.add_argument("--batch-a", action="store_true", help="Run Query Set A (5 regulatory & legal queries)")
    parser.add_argument("--queries", nargs="+", help="Custom queries to run")
    parser.add_argument("--output", type=str, default="batch_a_results.json", help="Output JSON filename")
    parser.add_argument("--iterations", type=int, default=0, help="Number of random keyword passes to run")

    args = parser.parse_args()

    batch_a_queries = [
        "Chase Kinslow CFPB complaint 260717-35668593",
        "Chase Kinslow Monroe Police Department report 26-29572",
        "Chase Kinslow regulatory-archive-2026 github",
        "Chase Kinslow Louisiana AG Liz Murrill dispute submission",
        "Chase Kinslow California AG Rob Bonta dispute notice"
    ]

    if args.batch_a:
        run_custom_queries(batch_a_queries, output_filename=args.output)
    elif args.queries:
        run_custom_queries(args.queries, output_filename=args.output)
    elif args.iterations > 0:
        all_passes = []
        for i in range(1, args.iterations + 1):
            p_res = run_search_pass(i, max_queries=5)
            all_passes.append(p_res)
            if i < args.iterations:
                print("\nWaiting 2 seconds before next keyword variation pass...")
                time.sleep(2)
        log_path = os.path.join(os.path.dirname(__file__), "search_audit_results.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(all_passes, f, indent=2)
        print(f"\nCompleted {args.iterations} pass(es). Results saved to {log_path}")
    else:
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            num_passes = int(sys.argv[1])
            all_passes = []
            for i in range(1, num_passes + 1):
                p_res = run_search_pass(i, max_queries=5)
                all_passes.append(p_res)
                if i < num_passes:
                    time.sleep(2)
            log_path = os.path.join(os.path.dirname(__file__), "search_audit_results.json")
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(all_passes, f, indent=2)
            print(f"\nCompleted {num_passes} pass(es). Results saved to {log_path}")
        else:
            print("Defaulting to Batch A queries execution...")
            run_custom_queries(batch_a_queries, output_filename=args.output)


