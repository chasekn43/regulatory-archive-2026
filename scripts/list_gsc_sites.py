from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

KEY_FILE = "google_console_key.json"
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

if not os.path.exists(KEY_FILE):
    print(f"Error: {KEY_FILE} not found!")
    exit(1)

try:
    credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
    service = build('searchconsole', 'v1', credentials=credentials)
    
    print("Listing Search Console sites...")
    site_list = service.sites().list().execute()
    
    sites = site_list.get('siteEntry', [])
    if not sites:
        print("No sites found verified under this credentials file.")
    else:
        print(f"Found {len(sites)} verified property/properties:")
        for s in sites:
            print(f"  - Site: {s.get('siteUrl')} | Permission: {s.get('permissionLevel')}")
            
except Exception as e:
    print("Error querying Search Console API:", e)
