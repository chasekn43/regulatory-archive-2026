import urllib.request
import urllib.parse
import re
from html import unescape
from fireprox_config import get_base_url, DIRECT_ENDPOINTS

q = "Affirm locked account Reddit"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

print("=== DIAGNOSING SEARCH ENGINE ENDPOINTS ===")

# 1. DuckDuckGo Lite
print("\n--- Testing DuckDuckGo Lite ---")
data = urllib.parse.urlencode({'q': q}).encode('utf-8')
req = urllib.request.Request("https://lite.duckduckgo.com/lite/", data=data, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        import re
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html)
        print("Total links found in DDG Lite:", len(links))
        for h, t in links:
            if "duckduckgo.com" not in h and not h.startswith("/"):
                print("DDG Link:", h, "->", t)
except Exception as e:
    print(f"Error: {e}")

# 2. Bing Direct
print("\n--- Testing Bing Direct ---")
b_url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
req = urllib.request.Request(b_url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        # Bing organic results are in <li class="b_algo">
        algos = re.findall(r'<li class="b_algo">(.*?)</li>', html, re.DOTALL)
        print("Bing b_algo blocks:", len(algos))
        if not algos:
            # Check h2 a hrefs
            h2_links = re.findall(r'<h2><a[^>]+href="([^"]+)"[^>]*>(.*?)</a></h2>', html, re.DOTALL)
            print("Bing h2 links:", len(h2_links))
            for h, t in h2_links[:5]:
                print("Bing Result:", h, "->", re.sub(r'<.*?>', '', t).strip())
        else:
            for b in algos[:5]:
                m = re.search(r'<h2><a[^>]+href="([^"]+)"[^>]*>(.*?)</a></h2>', b, re.DOTALL)
                if m:
                    print("Bing Algo:", m.group(1), "->", re.sub(r'<.*?>', '', m.group(2)).strip())
except Exception as e:
    print(f"Error: {e}")

# 3. Yahoo Direct
print("\n--- Testing Yahoo Direct ---")
y_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(q)}"
req = urllib.request.Request(y_url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        y_links = re.findall(r'<a[^>]+href="([^"]*r\.search\.yahoo\.com/[^"]*)"[^>]*>(.*?)</a>', html)
        print("Yahoo r.search redirect links:", len(y_links))
        for h, t in y_links[:5]:
            # decode yahoo redirect
            ru = re.search(r'/RU=([^/]+)/', h)
            decoded = urllib.parse.unquote(ru.group(1)) if ru else h
            print("Yahoo Result:", decoded, "->", re.sub(r'<.*?>', '', t).strip())
except Exception as e:
    print(f"Error: {e}")

# 4. Google
print("\n--- Testing Google ---")
g_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
req = urllib.request.Request(g_url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print("DDG HTML status:", resp.status)
except Exception as e:
    print(f"DDG HTML Error: {e}")

