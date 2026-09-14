"""
Google Indexing & Search Console Automation Suite

This script submits sitemaps and individual URLs directly to Google's Indexing API
and Google Search Console API.
"""

import os
import sys
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_credentials.json")
if not os.path.exists(KEY_FILE):
    KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_console_key.json")

SITEMAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitemap.xml")
SITE_URL = "https://kinslow-regulatory-archive.org/"
SCOPES = [
    'https://www.googleapis.com/auth/indexing',
    'https://www.googleapis.com/auth/webmasters'
]

def get_service_account_email():
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, 'r') as f:
                data = json.load(f)
                return data.get('client_email', 'gsc-indexer@regulatory-archive-2026.iam.gserviceaccount.com')
        except:
            pass
    return 'gsc-indexer@regulatory-archive-2026.iam.gserviceaccount.com'

def parse_sitemap():
    """Extracts all URLs from sitemap.xml."""
    urls = []
    if not os.path.exists(SITEMAP_FILE):
        print(f"[-] Sitemap not found at {SITEMAP_FILE}")
        return [SITE_URL]

    try:
        tree = ET.parse(SITEMAP_FILE)
        root = tree.getroot()
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        
        for url_elem in root.findall("ns:url", namespace):
            loc = url_elem.find("ns:loc", namespace)
            if loc is not None and loc.text:
                urls.append(loc.text.strip())

        print(f"[+] Parsed {len(urls)} URLs from sitemap.xml")
    except Exception as e:
        print(f"[-] Error parsing sitemap: {e}")
        urls = [SITE_URL]
    return urls

def submit_sitemap_to_gsc():
    if not os.path.exists(KEY_FILE):
        print(f"[-] Credentials file not found: {KEY_FILE}")
        return False
    try:
        credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=['https://www.googleapis.com/auth/webmasters'])
        webmasters_service = build('webmasters', 'v3', credentials=credentials)
        site_property = "sc-domain:kinslow-regulatory-archive.org"
        sitemap_url = "https://kinslow-regulatory-archive.org/sitemap.xml"
        
        webmasters_service.sitemaps().submit(siteUrl=site_property, feedpath=sitemap_url).execute()
        print(f"[+] Google Search Console: Successfully submitted {sitemap_url} for {site_property}")
        return True
    except Exception as e:
        print(f"[-] Google Search Console sitemap submission notice: {e}")
        return False

def inspect_url_gsc(url):
    if not os.path.exists(KEY_FILE):
        return None
    try:
        credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=['https://www.googleapis.com/auth/webmasters.readonly'])
        service = build('searchconsole', 'v1', credentials=credentials)
        body = {
            "inspectionUrl": url,
            "siteUrl": "sc-domain:kinslow-regulatory-archive.org"
        }
        res = service.urlInspection().index().inspect(body=body).execute()
        return res.get("inspectionResult", {}).get("indexStatusResult", {})
    except Exception as e:
        print(f"[-] GSC URL inspection notice for {url}: {e}")
        return None

def publish_to_google_indexing_api():
    if not os.path.exists(KEY_FILE):
        print(f"[-] Credentials file not found: {KEY_FILE}")
        return

    urls = parse_sitemap()
    print(f"[+] Loaded {len(urls)} URLs from sitemap for Google Indexing API push.")

    try:
        credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
        indexing_service = build('indexing', 'v3', credentials=credentials)
    except Exception as e:
        print(f"[-] Failed to initialize Google API client: {e}")
        return

    success_count = 0
    permission_needed = False
    sa_email = get_service_account_email()

    for idx, url in enumerate(urls, 1):
        print(f"[{idx}/{len(urls)}] Pushing URL to Google Indexing API: {url}")
        try:
            content = {
                'url': url,
                'type': 'URL_UPDATED'
            }
            res = indexing_service.urlNotifications().publish(body=content).execute()
            print(f"  [SUCCESS] Notified Google: {res.get('urlNotificationMetadata', {}).get('latestUpdate', {}).get('notifyTime')}")
            success_count += 1
            time.sleep(0.5)
        except Exception as e:
            err_str = str(e)
            if "Permission denied" in err_str or "403" in err_str:
                permission_needed = True
                print(f"  [-] Permission Notice: Service account requires Owner access in Google Search Console.")
                break
            else:
                print(f"  [-] Error: {e}")

    if permission_needed:
        print("\n" + "="*70)
        print(" FINAL STEP TO ACTIVATE GOOGLE SEARCH CONSOLE API ACCESS:")
        print(f" 1. Open Google Search Console: https://search.google.com/search-console")
        print(f" 2. Select property: kinslow-regulatory-archive.org")
        print(f" 3. Go to Settings -> Users and permissions -> Click 'Add user'")
        print(f" 4. Enter email: {sa_email}")
        print(f" 5. Set Permission to: Owner (or Full)")
        print("="*70 + "\n")
    else:
        print(f"\n[+] Successfully pushed {success_count} URLs to Google Indexing API.")

if __name__ == "__main__":
    print("=== Google Search Console & Indexing API Instant Pusher ===")
    publish_to_google_indexing_api()
