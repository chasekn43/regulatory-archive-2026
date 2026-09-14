import urllib.request
import urllib.parse
import re

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
headers = {
    "User-Agent": user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

def test_engine(name, url):
    print(f"=== Testing {name} ===")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            print(f"Status: {response.getcode()}, HTML length: {len(html)}")
            
            # Print sample tags or matching patterns
            if name == "Google":
                # Find links that look like search results
                links = re.findall(r'href="([^"]+)"', html)
                search_links = [l for l in links if "google.com" not in l and l.startswith("http")]
                print(f"Sample links found: {search_links[:5]}")
                
                # Check for h3
                h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', html)
                print(f"H3 count: {len(h3s)}, sample: {h3s[:3]}")
                
            elif name == "Bing":
                h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
                print(f"H2 count: {len(h2s)}")
                for h in h2s[:3]:
                    print(f"  H2: {h[:150]}")
                    
            elif name == "DuckDuckGo":
                urls = re.findall(r'href="([^"]+)"', html)
                print(f"URLs found count: {len(urls)}, sample: {urls[:10]}")
                # check result url
                res_urls = re.findall(r'class="result__url"[^>]*href="([^"]+)"', html)
                print(f"result__url count: {len(res_urls)}, sample: {res_urls[:3]}")
    except Exception as e:
        print(f"Error: {e}")

test_engine("Google", "https://www.google.com/search?q=Chase+Kinslow+Affirm")
test_engine("Bing", "https://www.bing.com/search?q=Chase+Kinslow+Affirm")
test_engine("DuckDuckGo", "https://html.duckduckgo.com/html/?q=Chase+Kinslow+Affirm")
