import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime

# Import existing credentials & keys
from push_to_google import submit_sitemap_to_gsc, inspect_url_gsc
from submit_indexnow import submit_to_indexnow, parse_sitemap

def sync_and_submit():
    print(f"=======================================================")
    print(f"  EXECUTING UNIFIED INDEXATION ENGINE ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"  Target Domain: https://kinslow-regulatory-archive.org")
    print(f"=======================================================\n")
    
    # 1. IndexNow Submission to Bing, Yahoo, Yandex, Naver
    print("[1/3] Notifying IndexNow & Bing/Yahoo network...")
    try:
        urls = parse_sitemap()
        submit_to_indexnow(urls)
    except Exception as e:
        print(f"IndexNow error: {e}")
        
    # 2. Google Search Console Sitemap Submission
    print("\n[2/3] Submitting Sitemap to Google Search Console API...")
    try:
        submit_sitemap_to_gsc()
    except Exception as e:
        print(f"GSC Sitemap error: {e}")
        
    # 3. Bing Webmaster Tools API Feed Submission
    print("\n[3/3] Submitting Feed to Bing Webmaster Tools API...")
    bing_api_key = "34b9bbd3b295468c8d754700c3750742"
    site_url = "http://kinslow-regulatory-archive.org/"
    feed_url = "https://kinslow-regulatory-archive.org/sitemap.xml"
    
    endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitFeed?apikey={bing_api_key}"
    payload = {
        "siteUrl": site_url,
        "feedUrl": feed_url
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"Bing Webmaster API Response: HTTP {resp.status} - Feed accepted")
    except Exception as e:
        print(f"Bing Webmaster Feed error: {e}")

    print("\nUnified Indexation execution complete across all search engines.")

if __name__ == '__main__':
    sync_and_submit()
