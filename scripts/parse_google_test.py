import urllib.request
import urllib.parse
import re

url = "https://www.google.com/search?q=Chase+Kinslow+Affirm&gbv=1"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read().decode('utf-8', errors='ignore')
        
    print("Fetched fresh Google page. Length:", len(html))
    
    # Print the first 10 href links
    hrefs = re.findall(r'href="([^"]+)"', html)
    print(f"Total href links found: {len(hrefs)}")
    print("Sample hrefs:")
    for h in hrefs[:30]:
        print(f"  - {h[:100]}")
        
    # Search specifically for "/url?"
    url_qs = [h for h in hrefs if "/url?" in h]
    print(f"Total /url? links: {len(url_qs)}")
    for u in url_qs[:10]:
        print(f"  - {u[:150]}")
        
except Exception as e:
    print(f"Error: {e}")
