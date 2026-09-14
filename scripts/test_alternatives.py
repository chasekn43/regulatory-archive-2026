import urllib.request
import urllib.parse
import re
from fireprox_config import get_base_url
from waf_bypass_headers import apply_bypass_headers

user_agents = {
    "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "mobile": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
}

def test_google_gbv():
    print("=== Testing Google with &gbv=1 ===")
    url = f"{get_base_url('google')}/search?q=Chase+Kinslow+Affirm&gbv=1"
    headers = {
        "User-Agent": user_agents["chrome"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            # Look for search result links
            # In basic Google HTML, links are under <a href="/url?q=URL">
            links = re.findall(r'href="/url\?q=([^&"]+)', html)
            print(f"Google gbv=1 link count: {len(links)}")
            for l in links[:5]:
                print(f"  Link: {urllib.parse.unquote(l)}")
    except Exception as e:
        print(f"Google gbv=1 error: {e}")

def test_ddg_lite():
    print("=== Testing DuckDuckGo Lite ===")
    url = f"{get_base_url('duckduckgo_lite')}/lite/"
    data = urllib.parse.urlencode({"q": "Chase+Kinslow+Affirm"}).encode('utf-8')
    headers = {
        "User-Agent": user_agents["chrome"],
        "Content-Type": "application/x-www-form-urlencoded"
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    apply_bypass_headers(req, mode='pro')
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            # Look for links
            # DDG Lite results have class="result-link" or are in a form
            links = re.findall(r'href="([^"]+)"', html)
            links = [l for l in links if "duckduckgo.com" not in l and not l.startswith("/")]
            print(f"DDG Lite link count: {len(links)}")
            for l in links[:5]:
                print(f"  Link: {l}")
    except Exception as e:
        print(f"DDG Lite error: {e}")

def test_bing_headers():
    print("=== Testing Bing with Full Headers ===")
    url = f"{get_base_url('bing')}/search?q=Chase+Kinslow+Affirm"
    headers = {
        "User-Agent": user_agents["chrome"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9,en;q=0.8",
        "Referer": "https://www.bing.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            links = re.findall(r'href="([^"]+)"', html)
            # Find external links
            ext_links = [l for l in links if l.startswith("http") and "bing.com" not in l and "live.com" not in l and "microsoft.com" not in l]
            print(f"Bing link count: {len(ext_links)}")
            for l in ext_links[:5]:
                print(f"  Link: {l}")
    except Exception as e:
        print(f"Bing error: {e}")

test_google_gbv()
test_ddg_lite()
test_bing_headers()
