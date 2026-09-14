import urllib.request
import json
import time

EXA_API_KEY = "47fee989-446a-44be-8aa0-733c1a688361"
url = "https://api.exa.ai/search"
payload = {
    "query": "Chase Kinslow Fintech BNPL merchant dispute",
    "useAutoprompt": False,
    "numResults": 10
}
headers = {
    "x-api-key": EXA_API_KEY,
    "Content-Type": "application/json"
}

print("Querying Exa search API...")
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
        print(f"Parsed {len(results)} results from Exa:")
        for idx, r in enumerate(results[:3], 1):
            print(f"  {idx}. Title: {r.get('title')} | URL: {r.get('url')}")
except Exception as e:
    print("Exa query failed:", e)
