import urllib.request
import urllib.parse
import re
import json
import base64
from html import unescape
from fireprox_config import get_base_url
from waf_bypass_headers import apply_bypass_headers

queries = [
    "Chase Kinslow Fintech BNPL merchant dispute",
    "Charles Kinslow CFPB Administrative Procedures Act",
    "Chase Kinslow customer service refund delays",
    "Charles Kinslow point of sale lines of credit",
    "Chase Kinslow CFPB complaint 260717-35668593",
    "Charles Kinslow CFPB complaint 260717-35668593",
    "Chase Kinslow Monroe Police Department report 26-29572",
    "Charles Kinslow Monroe Police Department report 26-29572",
    "Chase Kinslow Affirm dispute archive",
    "Charles Kinslow Affirm dispute archive",
    "Fintech BNPL merchant dispute CFPB complaint",
    "Administrative Procedures Act Buy Now Pay Later lines of credit",
    "Customer service refund delays BNPL loan dispute",
    "Monroe Police Department report 26-29572 Affirm fraud"
]

TARGET_INDICATORS = [
    "chasekn43",
    "regulatory-archive-2026",
    "regulatory-archive.kinslow.co",
    "kinslow.co",
    "260717-35668593",
    "26-29572"
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def clean_text(html_str):
    if not html_str:
        return ""
    cleanr = re.compile(r'<.*?>')
    cleantext = re.sub(cleanr, '', html_str)
    return unescape(cleantext).strip()

def decode_url(url):
    try:
        url = unescape(url)
        if "uddg=" in url:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if "uddg" in parsed:
                return parsed["uddg"][0]
        if "r.search.yahoo.com" in url and "/RU=" in url:
            match = re.search(r'/RU=([^/]+)/', url)
            if match:
                return urllib.parse.unquote(match.group(1))
    except Exception:
        pass
    return url

def search_ddg(query):
    url = f"{get_base_url('duckduckgo')}/html/?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<a class="result__url" href="(.*?)">(.*?)</a>', html)
            snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
            for i, (href, title) in enumerate(matches[:10]):
                dec_url = decode_url(href)
                snip = clean_text(snippets[i]) if i < len(snippets) else ""
                results.append({
                    "rank": i + 1,
                    "title": clean_text(title),
                    "url": dec_url,
                    "snippet": snip,
                    "is_target": any(ind in dec_url.lower() for ind in TARGET_INDICATORS)
                })
    except Exception as e:
        results.append({"error": str(e)})
    return results

def search_google(query):
    url = f"{get_base_url('google')}/search?q={urllib.parse.quote(query)}&num=10"
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            raw_links = re.findall(r'href="/url\?q=(http[s]?://[^&]+)&', html)
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html)
            rank = 1
            for i, l in enumerate(raw_links):
                dec_url = urllib.parse.unquote(l)
                if "google.com" not in dec_url and "youtube.com" not in dec_url:
                    t = clean_text(titles[i]) if i < len(titles) else "Google Result"
                    results.append({
                        "rank": rank,
                        "title": t,
                        "url": dec_url,
                        "snippet": "",
                        "is_target": any(ind in dec_url.lower() for ind in TARGET_INDICATORS)
                    })
                    rank += 1
    except Exception as e:
        results.append({"error": str(e)})
    return results

def search_bing(query):
    url = f"{get_base_url('bing')}/search?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<h2><a href="(http[s]?://[^"]+)"[^>]*>(.*?)</a></h2>', html)
            for i, (href, title) in enumerate(matches[:10]):
                dec_url = decode_url(href)
                results.append({
                    "rank": i + 1,
                    "title": clean_text(title),
                    "url": dec_url,
                    "snippet": "",
                    "is_target": any(ind in dec_url.lower() for ind in TARGET_INDICATORS)
                })
    except Exception as e:
        results.append({"error": str(e)})
    return results

def search_yahoo(query):
    url = f"{get_base_url('yahoo')}/search?p={urllib.parse.quote(query)}"
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    req = urllib.request.Request(url, headers=headers)
    apply_bypass_headers(req, mode='pro')
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<h3 class="title"><a href="(http[s]?://[^"]+)"[^>]*>(.*?)</a></h3>', html)
            for i, (href, title) in enumerate(matches[:10]):
                dec_url = decode_url(href)
                results.append({
                    "rank": i + 1,
                    "title": clean_text(title),
                    "url": dec_url,
                    "snippet": "",
                    "is_target": any(ind in dec_url.lower() for ind in TARGET_INDICATORS)
                })
    except Exception as e:
        results.append({"error": str(e)})
    return results

audit = {}
for q in queries:
    audit[q] = {
        "DuckDuckGo": search_ddg(q),
        "Google": search_google(q),
        "Bing": search_bing(q),
        "Yahoo": search_yahoo(q)
    }

with open("live_indexation_test.json", "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2)

print("Audit complete! Saved to live_indexation_test.json")
