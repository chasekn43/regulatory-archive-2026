import urllib.request
import urllib.parse
import json
import time
import re
import os
from fireprox_config import get_base_url
from waf_bypass_headers import apply_bypass_headers

# Target configuration
TARGET_DOMAIN = "kinslow-regulatory-archive.org"
TARGET_REPO = "regulatory-archive-2026"
FULL_TARGET_URL = f"https://{TARGET_DOMAIN}/"

KEYWORDS = [
    "Charles W. Kinslow Fintech BNPL merchant dispute",
    "Charles W. Kinslow IV CFPB Administrative Procedures Act",
    "Chase Kinslow customer service refund delays",
    "Charles Kinslow point of sale lines of credit",
    "Chase Kinslow Affirm evidence vault",
    "Regulation Z billing error procedures BNPL point of sale credit",
    "APA 5 U.S.C. 553 rulemaking exemption regulatory reliance interest",
    "CFPB UDAAP customer service refund delays fintech credit",
    "Uncredited ledger error SOX internal controls compliance",
    "Charles W. Kinslow IV attorney CPA fintech regulatory archive",
    "Charles K. Fintech BNPL merchant dispute",
    "Andy Chen Managing Counsel Affirm regulatory dispute",
    "Madison Marshall Morgan Lewis attorney representation",
    "Arjun Rao Morgan Lewis partner consumer dispute",
    "Morgan Lewis regulatory dispute Affirm",
    "CFPB interpretive rule withdrawal 2025",
    "CFPB BNPL dispute rules",
    "APA 5 U.S.C. 553 notice and comment exemption",
    "California UCL 17200 fintech billing dispute",
    "Louisiana AG consumer protection complaint",
    "automated fraud rejection decision trees",
    "fintech portal lockout payment workaround",
    "unresponsive fintech customer support loop"
]

ENGINES = {
    "DuckDuckGo": get_base_url('duckduckgo') + "/html/?q={}",
    "Bing": get_base_url('bing') + "/search?q={}",
    "Yahoo": get_base_url('yahoo') + "/search?p={}"
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def check_keyword_on_engine(engine_name, url_template, query):
    """Executes a single compliant query and checks for target domain in response."""
    encoded_query = urllib.parse.quote_plus(query)
    search_url = url_template.format(encoded_query)
    
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(search_url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            found_domain = TARGET_DOMAIN in html
            found_repo = TARGET_REPO in html
            
            return {
                "status": "SUCCESS",
                "http_code": response.status,
                "found_domain": found_domain,
                "found_repo": found_repo,
                "indexed": found_domain and found_repo
            }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "found_domain": False,
            "found_repo": False,
            "indexed": False
        }

def run_rank_check():
    print("=== GitHub Repository Search Rank Audit ===")
    print(f"Target Repository: {FULL_TARGET_URL}\n")
    
    results = {}
    
    for kw in KEYWORDS:
        print(f"[*] Auditing Query: '{kw}'")
        results[kw] = {}
        
        for engine_name, url_template in ENGINES.items():
            res = check_keyword_on_engine(engine_name, url_template, kw)
            results[kw][engine_name] = res
            
            status_icon = "[OK] FOUND" if res.get("indexed") else "[X] NOT FOUND"
            print(f"  - {engine_name:12s}: {status_icon}")
            
            # Politeness delay to ensure non-disruptive query rate
            time.sleep(2)
        print()

    # Save summary report
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rank_audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"[+] Audit complete. Report saved to: {report_path}")

if __name__ == "__main__":
    run_rank_check()
