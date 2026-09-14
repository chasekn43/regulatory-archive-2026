import os
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from fireprox_config import get_base_url, get_bing_indexnow_url
from waf_bypass_headers import apply_bypass_headers

# Configuration
KEY = "4366b539c9914619a970e53a2707ec41"
HOST = "kinslow-regulatory-archive.org"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
SITEMAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitemap.xml")
KEY_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{KEY}.txt")

def create_key_file():
    """Creates the IndexNow verification key file at the site root."""
    with open(KEY_FILE_PATH, "wb") as f:
        f.write(KEY.encode("utf-8"))
    print(f"[+] Key file created: {KEY_FILE_PATH}")

def parse_sitemap():
    """Extracts all URLs from sitemap.xml."""
    urls = []
    if not os.path.exists(SITEMAP_PATH):
        print(f"[-] Sitemap not found at {SITEMAP_PATH}")
        return [f"https://{HOST}/"]

    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    
    for url_elem in root.findall("ns:url", namespace):
        loc = url_elem.find("ns:loc", namespace)
        if loc is not None and loc.text:
            urls.append(loc.text.strip())

    print(f"[+] Parsed {len(urls)} URLs from sitemap.xml")
    return urls

def submit_to_indexnow(url_list):
    """Submits URLs to IndexNow API endpoints (notifies Bing, Yahoo, Yandex, Naver, Seznam)."""
    endpoints = [
        f"{get_base_url('indexnow')}/indexnow",
        get_bing_indexnow_url()
    ]
    
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": url_list
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    for endpoint in endpoints:
        print(f"[+] Submitting {len(url_list)} URLs to IndexNow API ({endpoint})...")
        try:
            req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
            apply_bypass_headers(req, mode='pro')
            with urllib.request.urlopen(req, timeout=15) as response:
                status = response.status
                print(f"[SUCCESS] {endpoint} Response Code: {status}")
                if status in [200, 202]:
                    print("[OK] Submission accepted by IndexNow engine grid.")
        except urllib.error.HTTPError as e:
            print(f"[-] {endpoint} Status: {e.code} ({e.reason})")
            try:
                body = e.read().decode('utf-8')
                print(f"    [Response Body] {body}")
            except Exception:
                pass
            if e.code == 403:
                print("    [NOTE] HTTP 403 indicates IndexNow crawler key validation failed.")
                print(f"    Confirm the key file is reachable at {KEY_LOCATION}, then fall back to Google Search Console & Bing Webmaster Tools XML Sitemap submission: https://{HOST}/sitemap.xml")
        except Exception as e:
            print(f"[-] {endpoint} Submission Error: {e}")

    # Fallback GET pings for each URL
    print("[+] Issuing GET pings for each URL to IndexNow...")
    for target_url in url_list:
        get_url = f"{get_bing_indexnow_url()}?url={urllib.parse.quote(target_url)}&key={KEY}"
        try:
            req = urllib.request.Request(get_url, headers={"User-Agent": headers["User-Agent"]})
            apply_bypass_headers(req, mode='pro')
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"  - Ping {target_url}: Status {resp.status}")
        except Exception as e:
            print(f"  - Ping {target_url}: {e}")

    # Google Search Console Note
    sitemap_url = f"https://{HOST}/sitemap.xml"
    print(f"[+] Google Search Console Sitemap URL: {sitemap_url}")
    print("[NOTE] Direct HTTP GET sitemap pinging was officially deprecated by Google. Submit sitemap via Google Search Console web console or API.")

if __name__ == "__main__":
    print("=== IndexNow & Search Engine Instant Submission ===")
    create_key_file()
    urls = parse_sitemap()
    submit_to_indexnow(urls)
