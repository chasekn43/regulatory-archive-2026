import urllib.request
import urllib.parse
import urllib.error
import random
import time
import re
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from fireprox_config import get_base_url
from waf_bypass_headers import apply_bypass_headers

# Configuration Flags
USE_PROXY = False  # Set to False to run direct requests over local VPN (recommended to bypass public proxy blockages/timeouts)

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "search_continuous.log")

# Setup Logging
def log_message(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}\n"
    print(log_line.strip())
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Failed writing to log: {e}")

# Data sources for query generation (broad tangential regulatory & fintech keywords)
names = [
    "Charles W. Kinslow IV",
    "Charles W. Kinslow",
    "Charles Kinslow IV",
    "Charles Kinslow",
    "Chase Kinslow",
    "Charles K.",
    "Charles K",
    "chasekn43",
    "chasekn",
    "kinslow",
    "Andy Chen Affirm",
    "Andy Chen Managing Counsel",
    "Madison Marshall",
    "Madison Marshall Morgan Lewis",
    "Arjun Rao",
    "Arjun Rao Morgan Lewis",
    "Morgan Lewis"
]

keywords = [
    "4q8isr1",
    "LinkedIn",
    "fintech",
    "BNPL",
    "merchant dispute",
    "CFPB",
    "Administrative Procedures Act",
    "customer service",
    "refund delays",
    "lines of credit",
    "point-of-sale financing",
    "APA challenge consumer finance",
    "credit line dispute regulation z",
    "CFPB complaint BNPL merchant",
    "regulation z",
    "consumer fraud protection bureau",
    "lockout",
    "credit",
    "frozen accounts",
    "regulatory",
    "security freeze",
    "credit lock",
    "frozen credit file",
    "FCRA dispute",
    "billing error notice",
    "unauthorized billing charge",
    "account lockout dispute",
    "suspended credit line",
    "merchant settlement dispute",
    "Fair Credit Reporting Act dispute",
    "Truth in Lending Act disclosure",
    "Regulation E error resolution",
    "adverse action notice credit denial",
    "CFPB complaint portal",
    "merchant chargeback clearing friction",
    "arbitrary account suspension fintech",
    "CFPB regulatory circular",
    "Dodd-Frank Title X UDAAP compliance",
    "Regulation Z 12 C.F.R. 1026",
    "merchant cancellation refund dispute",
    "holder in due course rule retail finance",
    "point-of-sale financing error resolution",
    "credit reporting disputes retail credit",
    "unsolicited marketing SMS compliance",
    "automated fraud rejection audit",
    "merchant refund clearing delays",
    "managing counsel cease and desist directive",
    "outside counsel representation ethics notice",
    "Rule 4.2 ethical notice consumer finance",
    "unsolicited team email outreach",
    "regulatory-archive-2026",
    "fintech compliance archive",
    "BNPL regulatory record",
    "CFPB interpretive rule withdrawal 2025",
    "CFPB BNPL dispute rules",
    "APA 5 U.S.C. 553 notice and comment exemption",
    "California UCL 17200 fintech billing dispute",
    "Louisiana AG consumer protection complaint",
    "automated fraud rejection decision trees",
    "fintech portal lockout payment workaround",
    "unresponsive fintech customer support loop"
]

# Engine configuration with urls
engines = [
    {"name": "Google", "url": f"{get_base_url('google')}/search?q={{}}"},
    {"name": "Bing", "url": f"{get_base_url('bing')}/search?q={{}}"},
    {"name": "Yahoo", "url": f"{get_base_url('yahoo')}/search?p={{}}"},
    {"name": "DuckDuckGo", "url": f"{get_base_url('duckduckgo')}/html/?q={{}}"}
]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36"
]

# Custom Redirect Handler to disable automatic redirect following.
class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, "Redirect Blocked (Suspected CAPTCHA/ISP Hijack)", headers, fp)
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302

# Thread-safe engine-specific verified pools
verified_pools = {
    "Google": set(),
    "Bing": set(),
    "Yahoo": set(),
    "DuckDuckGo": set()
}
verified_lock = threading.Lock()

# Cache variables for raw proxy list to avoid API rate-limiting
raw_proxies_cache = []
last_fetch_time = 0
cache_lock = threading.Lock()

def generate_random_ip():
    return f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

def get_raw_proxies():
    global last_fetch_time, raw_proxies_cache
    now = time.time()
    
    with cache_lock:
        if now - last_fetch_time < 90 and raw_proxies_cache:
            log_message("[VALIDATOR] Using cached raw proxies (API cooldown active)...")
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
            req = urllib.request.Request(url, headers={'User-Agent': random.choice(user_agents)})
            with urllib.request.urlopen(req, timeout=8) as response:
                content = response.read().decode('utf-8', errors='ignore')
                found = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}\b', content)
                raw_list.extend(found)
        except Exception as e:
            log_message(f"[API ERROR] Proxy fetch failed for {url}: {e}")
            
    with cache_lock:
        if raw_list:
            raw_proxies_cache = list(set(raw_list))
            last_fetch_time = now
        return raw_proxies_cache

def test_single_proxy(proxy):
    # Strict 1.5s timeout for validation checks
    timeout = 1.5
    
    # We test Bing, DuckDuckGo, Google, and Yahoo with active queries
    tests = [
        {"name": "Google", "url": f"{get_base_url('google')}/search?q=test"},
        {"name": "Bing", "url": f"{get_base_url('bing')}/search?q=test"},
        {"name": "Yahoo", "url": f"{get_base_url('yahoo')}/search?p=test"},
        {"name": "DuckDuckGo", "url": f"{get_base_url('duckduckgo')}/html/?q=test"}
    ]
    
    # Randomize test execution order to avoid sequential hotspotting
    random.shuffle(tests)
    
    for test in tests:
        name = test["name"]
        test_url = test["url"]
        try:
            proxy_support = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_support, NoRedirectHandler())
            req = urllib.request.Request(test_url, headers={'User-Agent': random.choice(user_agents)})
            with opener.open(req, timeout=timeout) as resp:
                if resp.status == 200:
                    with verified_lock:
                        verified_pools[name].add(proxy)
                    log_message(f"[VALIDATOR SUCCESS] Proxy {proxy} verified for {name}")
        except Exception:
            # Silent filter of noisy validator drops to keep stdout clean
            pass

def proxy_validator_thread():
    while True:
        with verified_lock:
            counts = {name: len(pool) for name, pool in verified_pools.items()}
            
        # Replenish if any engine pool is low
        if any(count < 15 for count in counts.values()):
            raw_proxies = get_raw_proxies()
            if raw_proxies:
                local_list = list(raw_proxies)
                random.shuffle(local_list)
                with ThreadPoolExecutor(max_workers=45) as executor:
                    executor.map(test_single_proxy, local_list[:150])
                
        time.sleep(10)

query_counter = 0
recent_queries = []

generic_affirm_queries = [
    "Affirm loan dispute resolution",
    "Affirm CFPB complaint rebuttal",
    "Affirm billing error Regulation Z",
    "Affirm refund delays merchant dispute",
    "Affirm customer service phone complaints",
    "Affirm unauthorized charges fraud report",
    "Affirm Morgan Lewis outside counsel",
    "Affirm Andy Chen managing counsel",
    "Affirm Scott Williams client success",
    "Affirm Max Levchin regulatory scrutiny",
    "Affirm police report carrier delivery dispute",
    "Affirm point of sale lines of credit dispute",
    "Affirm SOX 404 internal controls audit",
    "Affirm Louisiana AG consumer dispute",
    "Affirm California UCL 17200 unfair competition",
    "Affirm CFPB circular BNPL credit card",
    "Affirm bank billpay payment lockout",
    "Affirm Perfume Empire tracking 1LSDCR10011QF38",
    "CFPB Complaint 260717-35668593",
    "CFPB Complaint 260805-36566273",
    "Monroe Police Department report 26-29572",
    "Buy Now Pay Later billing error resolution procedures",
    "12 CFR 1026.13 closed-end installment dispute",
    "APA 5 U.S.C. 553 notice and comment fintech rulemaking",
    "FTC Holder in Due Course Rule 16 CFR 433 point of sale lending",
    "California Business and Professions Code 17200 fintech billing",
    "Sarbanes Oxley 404 retail installment loan ledger reconciliation",
    "Fintech point of sale dispute portal lockout workaround",
    "Affirm false response CFPB complaint",
    "Affirm liability clearance directive",
    "Affirm managing counsel cease and desist letter",
    "Affirm 3PL carrier delivery dispute proof",
    "Affirm unapplied merchant refund ledger loop"
]

def generate_query():
    global query_counter, recent_queries
    query_counter += 1
    
    fintech_terms = ["Affirm", "fintech", "BNPL", "buy now pay later", "lines of credit"]
    
    for _ in range(50):
        dice = random.random()
        
        # 45% Strategy: Pure Generic Affirm / Regulatory / Dispute Query (NO user name)
        if dice < 0.45:
            base_q = random.choice(generic_affirm_queries)
            if random.random() < 0.3:
                query = f'"{base_q}"'
            else:
                query = base_q
                
        # 30% Strategy: Entity Co-Occurrence (Affirm + Kinslow / Vault)
        elif dice < 0.75:
            name = random.choice(names[:10]) # Kinslow variations
            kw = random.choice([
                "Affirm dispute",
                "Affirm CFPB complaint",
                "Affirm regulatory archive",
                "Affirm billing error",
                "Affirm cease and desist",
                "Affirm customer service",
                "Affirm merchant refund",
                "Affirm loan default rebuttal",
                "Affirm police report 26-29572",
                "Affirm Morgan Lewis",
                "Affirm Andy Chen"
            ])
            if random.random() < 0.3:
                query = f'"{name}" "{kw}"'
            else:
                query = f"{name} {kw}"
                
        # 15% Strategy: Statutory & Legal Analysis Deep-Dives
        elif dice < 0.90:
            statutory = random.choice([
                "Regulation Z 12 CFR 1026.13 billing error",
                "APA 5 U.S.C. 553 notice and comment exemption",
                "California UCL 17200 fintech unfair competition",
                "SOX 404 internal controls retail installment lending",
                "TILA closed-end credit dispute disclosures",
                "Holder in Due Course Rule 16 CFR 433 merchant dispute"
            ])
            query = statutory
            
        # 10% Strategy: Professional & Jurisdictional Anchor
        else:
            name = random.choice(names)
            other_kw = random.choice(keywords)
            query = f"{name} {other_kw}"
        
        # Avoid running duplicate queries consecutively
        words = set(query.lower().replace('"', '').split())
        is_duplicate = False
        for old_q in recent_queries:
            old_words = set(old_q.lower().replace('"', '').split())
            if len(words) > 0 and len(old_words) > 0:
                intersection = words.intersection(old_words)
                if len(intersection) / max(len(words), 1) > 0.8:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            recent_queries.append(query)
            if len(recent_queries) > 30:
                recent_queries.pop(0)
            return query
            
    # Fallback
    return random.choice(generic_affirm_queries)
def main():
    if USE_PROXY:
        log_message("Continuous search simulator initialized with SSL filtering, Redirect blocking, and public proxy pools.")
        # Start the validator thread
        validator = threading.Thread(target=proxy_validator_thread, daemon=True)
        validator.start()
        
        log_message("Waiting for validator thread to verify active SSL proxies...")
        for _ in range(30):
            with verified_lock:
                total_verified = sum(len(pool) for pool in verified_pools.values())
                if total_verified > 0:
                    break
            time.sleep(1)
    else:
        log_message("Continuous search simulator initialized in DIRECT / VPN Mode (Bypassing public proxies).")

    # Attempt to start external tools launcher so repository tools are available to the search runner.
    try:
        launcher = r"C:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\run_all_tools.ps1"
        if os.path.exists(launcher):
            log_message(f"Starting external tools launcher: {launcher}")
            import subprocess
            # Start launcher detached so it runs concurrently with this process
            subprocess.Popen([
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                launcher
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        else:
            log_message(f"Launcher not found: {launcher}")
    except Exception as e:
        log_message(f"Failed to start launcher: {e}")

    while True:
        query = generate_query()
        
        # Bias engine weights: Bing 45%, DuckDuckGo 45%, Google 5%, Yahoo 5%
        engine = random.choices(
            engines, 
            weights=[5, 45, 5, 45], 
            k=1
        )[0]
        
        if not USE_PROXY:
            # Execute direct query over local VPN network connection
            ua = random.choice(user_agents)
            encoded_query = urllib.parse.quote_plus(query)
            search_url = engine["url"].format(encoded_query)
            
            headers = {
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive"
            }
            if engine["name"] == "DuckDuckGo":
                headers["Referer"] = f"{get_base_url('duckduckgo')}/"
                headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            elif engine["name"] == "Bing":
                headers["Referer"] = f"{get_base_url('bing')}/"
            elif engine["name"] == "Google":
                headers["Referer"] = f"{get_base_url('google')}/"
            elif engine["name"] == "Yahoo":
                headers["Referer"] = f"{get_base_url('yahoo')}/"
            
            opener = urllib.request.build_opener(NoRedirectHandler())
            urllib.request.install_opener(opener)
            
            start_time = time.time()
            try:
                req = urllib.request.Request(search_url, headers=headers)
                apply_bypass_headers(req, mode='pro')
                with urllib.request.urlopen(req, timeout=10.0) as response:
                    html = response.read()
                    elapsed = time.time() - start_time
                    log_message(f"[QUERY SUCCESS] {engine['name']} (Direct/VPN) returned {response.status} (Length: {len(html)}, Time: {elapsed:.2f}s) for query: '{query}'")
            except Exception as e:
                elapsed = time.time() - start_time
                log_message(f"[QUERY FAILED] {engine['name']} (Direct/VPN) failed in {elapsed:.2f}s: {e}")
        else:
            # Proxy query logic
            success = False
            max_attempts = 20
            
            for attempt in range(1, max_attempts + 1):
                with verified_lock:
                    available_engines = [e for e in engines if len(verified_pools[e["name"]]) > 0]
                    
                if not available_engines:
                    log_message(f"[QUERY PAUSE] No verified proxies available for any engine. Waiting...")
                    time.sleep(2)
                    continue
                    
                active_engine = engine
                if active_engine["name"] not in [e["name"] for e in available_engines]:
                    active_engine = random.choice(available_engines)
                    
                with verified_lock:
                    proxies_list = list(verified_pools[active_engine["name"]])
                    
                proxy = random.choice(proxies_list)
                ua = random.choice(user_agents)
                
                encoded_query = urllib.parse.quote_plus(query)
                search_url = active_engine["url"].format(encoded_query)
                
                fake_ip = generate_random_ip()
                headers = {
                    "User-Agent": ua,
                    "X-Forwarded-For": fake_ip,
                    "Client-IP": fake_ip,
                    "Via": fake_ip,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Connection": "keep-alive"
                }
                if active_engine["name"] == "DuckDuckGo":
                    headers["Referer"] = f"{get_base_url('duckduckgo')}/"
                    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                elif active_engine["name"] == "Bing":
                    headers["Referer"] = f"{get_base_url('bing')}/"
                elif active_engine["name"] == "Google":
                    headers["Referer"] = f"{get_base_url('google')}/"
                elif active_engine["name"] == "Yahoo":
                    headers["Referer"] = f"{get_base_url('yahoo')}/"
                
                proxy_support = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
                opener = urllib.request.build_opener(proxy_support, NoRedirectHandler())
                urllib.request.install_opener(opener)
                
                start_time = time.time()
                try:
                    req = urllib.request.Request(search_url, headers=headers)
                    apply_bypass_headers(req, mode='pro')
                    with urllib.request.urlopen(req, timeout=4.0) as response:
                        html = response.read()
                        elapsed = time.time() - start_time
                        log_message(f"[QUERY SUCCESS] {active_engine['name']} ({proxy}) returned {response.status} (Length: {len(html)}, Time: {elapsed:.2f}s) for query: '{query}' (Attempt {attempt})")
                        success = True
                        break
                except Exception as e:
                    elapsed = time.time() - start_time
                    log_message(f"[QUERY ATTEMPT FAILED] {active_engine['name']} ({proxy}) failed in {elapsed:.2f}s (Attempt {attempt}/{max_attempts}): {e}")
                    with verified_lock:
                        if proxy in verified_pools[active_engine["name"]]:
                            verified_pools[active_engine["name"]].remove(proxy)
                            
            if not success:
                log_message(f"[QUERY ABORTED] Query '{query}' failed to execute after {max_attempts} attempts.")
                
        # Random sleep delay between search iterations to emulate human browse pacing
        time.sleep(random.uniform(5.0, 15.0))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("Search simulator stopped by user.")
        sys.exit(0)
