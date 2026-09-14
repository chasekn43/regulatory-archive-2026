import urllib.request
import urllib.parse
import re

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
headers = {
    "User-Agent": user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

def download_and_inspect(name, url, filename):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[{name}] Downloaded to {filename}. Length: {len(html)}")
            
            # Show a brief preview of elements
            links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
            print(f"[{name}] Total links matching <a href...>: {len(links)}")
            for href, text in links[:5]:
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                print(f"  - Link: {href} | Text: {clean_text[:50]}")
    except Exception as e:
        print(f"[{name}] Error: {e}")

download_and_inspect("Google", "https://www.google.com/search?q=Chase+Kinslow+Affirm", "google_test.html")
download_and_inspect("Bing", "https://www.bing.com/search?q=Chase+Kinslow+Affirm", "bing_test.html")
download_and_inspect("DuckDuckGo", "https://html.duckduckgo.com/html/?q=Chase+Kinslow+Affirm", "ddg_test.html")
