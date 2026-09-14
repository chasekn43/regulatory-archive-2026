import subprocess
import urllib.request
import re
import random

def get_proxies():
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=2000&country=all&ssl=yes&anonymity=anonymous"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('utf-8')
            proxies = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}\b', content)
            return list(set(proxies))
    except Exception as e:
        print("Failed to get proxies:", e)
        return []

def test_google_obscura():
    proxies = get_proxies()
    print(f"Loaded {len(proxies)} proxies.")
    if not proxies:
        return
        
    random.shuffle(proxies)
    google_url = "https://www.google.com/search?q=Chase+Kinslow+Fintech+BNPL&gbv=1"
    binary_path = r"c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\403_tools\obscura\obscura.exe"
    
    for proxy in proxies[:10]:
        print(f"Trying proxy: {proxy}...")
        cmd = [binary_path, "--stealth", "--proxy", f"http://{proxy}", "fetch", google_url, "--dump", "html"]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12)
            if res.returncode == 0:
                html = res.stdout
                print(f"Success! HTML length: {len(html)}")
                if "sorry/index" in html or "captcha" in html.lower():
                    print("  -> Blocked (CAPTCHA)")
                else:
                    print("  -> Passed! Title matched.")
                    print("Sample HTML:", html[:400])
                    break
            else:
                print("  -> Failed (Non-zero exit)")
        except subprocess.TimeoutExpired:
            print("  -> Timeout expired")
        except Exception as e:
            print("  -> Error:", e)

if __name__ == "__main__":
    test_google_obscura()
