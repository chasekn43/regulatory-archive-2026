import urllib.request
import json
import time

TAVILY_API_KEY = "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"
url = "https://api.tavily.com/search"
payload = {
    "api_key": TAVILY_API_KEY,
    "query": "Chase Kinslow Fintech BNPL merchant dispute",
    "search_depth": "basic"
}
headers = {"Content-Type": "application/json"}

print("Querying Tavily search API...")
try:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"Status Code: {response.status}")
        results = data.get("results", [])
        print(f"Parsed {len(results)} results from Tavily:")
        for idx, r in enumerate(results[:3], 1):
            print(f"  {idx}. Title: {r.get('title')} | URL: {r.get('url')}")
except Exception as e:
    print("Tavily query failed:", e)
