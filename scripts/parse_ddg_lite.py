import urllib.request
import urllib.parse
import re

url = "https://lite.duckduckgo.com/lite/"
data = urllib.parse.urlencode({"q": "Chase Kinslow Affirm"}).encode('utf-8')
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

req = urllib.request.Request(url, data=data, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read().decode('utf-8', errors='ignore')
        
    print("Fetched DDG Lite page. Length:", len(html))
    
    links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
    print(f"Links count: {len(links)}")
    for href, text in links[:20]:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        print(f"  HREF: {href[:120]} | TEXT: {clean_text[:50]}")
        
except Exception as e:
    print(f"Error: {e}")
