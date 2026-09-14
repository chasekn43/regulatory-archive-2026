from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import xml.etree.ElementTree as ET
import json
import time
from datetime import datetime
import urllib.parse

# Configurations
KEY_FILE = "google_console_key.json"
SITEMAP_FILE = "sitemap.xml"
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
SITE_URL = "https://kinslow-regulatory-archive.org/"
CURR_CONV_ID = "89546ed0-656f-4d27-8a0e-d24a1b42b662"
ARTIFACT_DIR = os.path.join(r"C:\Users\Charwiz43\.gemini\antigravity\brain", CURR_CONV_ID)
REPORT_NAME = "gsc_indexing_report.md"

def parse_sitemap():
    urls = []
    if not os.path.exists(SITEMAP_FILE):
        print(f"Error: {SITEMAP_FILE} not found!")
        return urls
        
    try:
        tree = ET.parse(SITEMAP_FILE)
        root = tree.getroot()
        # Handle namespace
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_node in root.findall('ns:url', ns):
            loc = url_node.find('ns:loc', ns)
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
    except Exception as e:
        print("Error parsing sitemap:", e)
    return urls

def inspect_urls():
    if not os.path.exists(KEY_FILE):
        print(f"Error: Credentials key {KEY_FILE} not found!")
        return
        
    urls = parse_sitemap()
    print(f"Loaded {len(urls)} URLs from sitemap.")
    if not urls:
        return
        
    try:
        credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
        service = build('searchconsole', 'v1', credentials=credentials)
    except Exception as e:
        print("Failed to initialize Google Search Console client:", e)
        return

    results = []
    
    # We inspect each URL. GSC API limits: 2000 per day. We have ~20 URLs.
    for idx, url in enumerate(urls, 1):
        print(f"[{idx}/{len(urls)}] Inspecting URL: {url}")
        try:
            body = {
                "inspectionUrl": url,
                "siteUrl": SITE_URL
            }
            # Execute inspection
            response = service.urlInspection().index().inspect(body=body).execute()
            inspect_result = response.get("inspectionResult", {})
            index_status = inspect_result.get("indexStatusResult", {})
            
            # Extract metrics
            verdict = index_status.get("verdict", "UNKNOWN")
            coverage = index_status.get("coverageState", "Unknown status")
            crawl_time = index_status.get("lastCrawlTime", "Never")
            crawled_as = index_status.get("crawledAs", "N/A")
            robots_status = index_status.get("robotsTxtState", "N/A")
            indexing_state = index_status.get("indexingState", "N/A")
            
            results.append({
                "url": url,
                "verdict": verdict,
                "coverage_state": coverage,
                "last_crawl_time": crawl_time,
                "crawled_as": crawled_as,
                "robots_status": robots_status,
                "indexing_state": indexing_state
            })
            
            # Politeness delay to avoid hitting GSC limits too rapidly
            time.sleep(1)
            
        except Exception as e:
            print(f"  - Error inspecting {url}: {e}")
            results.append({
                "url": url,
                "verdict": "ERROR",
                "coverage_state": str(e),
                "last_crawl_time": "N/A",
                "crawled_as": "N/A",
                "robots_status": "N/A",
                "indexing_state": "N/A"
            })
            
    # Save raw inspection JSON
    with open("gsc_indexation_status.json", "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2)
        
    generate_md_report(results)

def generate_md_report(results):
    indexed_count = sum(1 for r in results if r["verdict"] == "PASS")
    total_count = len(results)
    
    md = []
    md.append("# 📈 Google Search Console (GSC) Indexation Audit")
    md.append(f"\n> **Last Audit Time**: {datetime.now().isoformat()} (Checked via GSC API)")
    md.append(f"> **Overall Indexation Status**: `{indexed_count} / {total_count} URLs Indexed` ({round(indexed_count/max(total_count, 1)*100, 1)}%)\n")
    
    md.append("## 📊 Indexation Coverage Breakdown")
    md.append("| Page / Document URL | Verdict | Detailed Status / Coverage | Last Crawl Time | Crawled As |")
    md.append("| :--- | :---: | :--- | :---: | :---: |")
    
    for r in results:
        # Style verdict
        v = r["verdict"]
        if v == "PASS":
            verdict_str = "🟢 **INDEXED**"
        elif v == "NEUTRAL":
            verdict_str = "🟡 **EXCLUDED / NEUTRAL**"
        elif v == "PARTIAL":
            verdict_str = "🟡 **PARTIAL INDEX**"
        elif v == "FAIL":
            verdict_str = "🔴 **FAIL / NOT INDEXED**"
        elif v == "ERROR":
            verdict_str = "🔴 **API ERROR**"
        else:
            verdict_str = f"⚪ {v}"
            
        # Get relative page path for readability
        parsed_url = urllib.parse.urlparse(r["url"])
        rel_path = parsed_url.path.replace("/regulatory-archive-2026/", "")
        if not rel_path:
            rel_path = "/"
            
        md.append(f"| [{rel_path}]({r['url']}) | {verdict_str} | {r['coverage_state']} | {r['last_crawl_time']} | {r['crawled_as']} |")
        
    # Add help context
    md.append("\n## 💡 GSC Status Descriptions")
    md.append("- 🟢 **GOOD**: Page is successfully indexed and can appear in search queries.")
    md.append("- 🟡 **Crawled - currently not indexed**: Google has crawled the page but decided not to add it to the index yet. This is common for brand new content and usually resolves with internal linking or submission updates.")
    md.append("- 🟡 **Discovered - currently not indexed**: Google found the page but has not crawled it yet. Typically means Google is prioritizing other crawls first.")
    
    # Save to artifact directory
    if os.path.exists(ARTIFACT_DIR):
        report_path = os.path.join(ARTIFACT_DIR, REPORT_NAME)
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write("\n".join(md))
        print(f"Markdown report generated successfully at: {report_path}")
    else:
        print("Artifact directory does not exist yet. Written locally.")

def rebuild_report_from_json():
    json_path = "gsc_indexation_status.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            results = data.get("results", [])
            if results:
                generate_md_report(results)
                print("Rebuilt report from GSC cache file.")
                return True
        except Exception as e:
            print("Failed to rebuild from cache:", e)
    return False

if __name__ == "__main__":
    import sys
    if "--rebuild" in sys.argv:
        if not rebuild_report_from_json():
            inspect_urls()
    else:
        inspect_urls()
