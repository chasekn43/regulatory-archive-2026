from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

KEY_FILE = "google_console_key.json"
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
SITE_URL = "https://kinslow-regulatory-archive.org/"

if not os.path.exists(KEY_FILE):
    print("GSC credentials JSON file not found.")
    exit(1)

try:
    credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
    service = build('searchconsole', 'v1', credentials=credentials)
    
    # Check search analytics for last 30 days
    request = {
        'startDate': '2026-07-01',
        'endDate': '2026-08-11',
        'dimensions': ['page'],
        'rowLimit': 100
    }
    
    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
    rows = response.get('rows', [])
    print(f"Total pages with active Search Analytics metrics: {len(rows)}")
    for r in rows:
        print(f"  - Page: {r['keys'][0]} | Clicks: {r.get('clicks', 0)} | Impressions: {r.get('impressions', 0)} | Position: {round(r.get('position', 0), 1)}")
        
except Exception as e:
    print("Failed to query Search Console Analytics API:", e)
