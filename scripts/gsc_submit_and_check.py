import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'google_console_key.json')
creds = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=['https://www.googleapis.com/auth/webmasters'])
service = build('webmasters', 'v3', credentials=creds)

site_url = 'https://chasekn43.github.io/regulatory-archive-2026/'
feed_url = 'https://chasekn43.github.io/regulatory-archive-2026/sitemap.xml'
feed_txt = 'https://chasekn43.github.io/regulatory-archive-2026/sitemap.txt'

try:
    service.sitemaps().submit(siteUrl=site_url, feedpath=feed_url).execute()
    print('SUCCESS: Submitted sitemap.xml to Google Search Console API!')
except Exception as e:
    print('Error submitting sitemap.xml:', e)

try:
    service.sitemaps().submit(siteUrl=site_url, feedpath=feed_txt).execute()
    print('SUCCESS: Submitted sitemap.txt to Google Search Console API!')
except Exception as e:
    print('Error submitting sitemap.txt:', e)

try:
    sitemaps = service.sitemaps().list(siteUrl=site_url).execute()
    print('\nCurrent registered sitemaps in GSC:')
    for sm in sitemaps.get('sitemap', []):
        path = sm.get('path')
        last_dl = sm.get('lastDownloaded')
        last_sub = sm.get('lastSubmitted')
        warns = sm.get('warnings')
        errs = sm.get('errors')
        print(f"  - Path: {path}")
        print(f"    Submitted: {last_sub} | Downloaded: {last_dl} | Errors: {errs} | Warnings: {warns}")
except Exception as e:
    print('Error listing sitemaps:', e)
